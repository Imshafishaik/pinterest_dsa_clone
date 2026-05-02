from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_, or_
from database.models import Pin, User, Like, Save, Tag, Interaction
from database.connection import db_manager, cache_manager, CACHE_KEYS
import json
from datetime import datetime, timedelta

class PinService:
    
    def __init__(self):
        self.cache = cache_manager
    
    def get_pin_by_id(self, pin_id: int) -> Optional[Pin]:
        cache_key = CACHE_KEYS['PIN'].format(id=pin_id)
        
        cached_pin = self.cache.get(cache_key)
        if cached_pin:
            return json.loads(cached_pin)
        
        with db_manager.get_session() as session:
            pin = session.query(Pin).options(
                joinedload(Pin.creator),
                joinedload(Pin.tags),
                joinedload(Pin.likes),
                joinedload(Pin.saves),
                joinedload(Pin.comments)
            ).filter(Pin.id == pin_id, Pin.is_active == True).first()
            
            if pin:
                pin_data = self._serialize_pin(pin)
                self.cache.set(cache_key, json.dumps(pin_data), ttl=3600)
                return pin_data
        
        return None
    
    def get_all_pins(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        with db_manager.get_session() as session:
            pins = session.query(Pin).options(
                joinedload(Pin.creator),
                joinedload(Pin.tags)
            ).filter(Pin.is_active == True, Pin.is_public == True)\
             .order_by(desc(Pin.created_at))\
             .limit(limit)\
             .offset(offset)\
             .all()
            
            return [self._serialize_pin(pin) for pin in pins]
    
    def get_user_pins(self, user_id: int, limit: int = 20, offset: int = 0) -> List[Dict]:
        with db_manager.get_session() as session:
            pins = session.query(Pin).options(
                joinedload(Pin.tags)
            ).filter(
                Pin.creator_id == user_id,
                Pin.is_active == True,
                Pin.is_public == True
            ).order_by(desc(Pin.created_at))\
             .limit(limit)\
             .offset(offset)\
             .all()
            
            return [self._serialize_pin(pin) for pin in pins]
    
    def search_pins(self, query: str, limit: int = 20, category: str = None) -> List[Dict]:
        cache_key = CACHE_KEYS['SEARCH_RESULTS'].format(query=f"search:{query}:{category}:{limit}")
        
        cached_results = self.cache.get(cache_key)
        if cached_results:
            return json.loads(cached_results)
        
        with db_manager.get_session() as session:
            search_filter = or_(
                Pin.title.ilike(f'%{query}%'),
                Pin.description.ilike(f'%{query}%'),
                Pin.category.ilike(f'%{query}%')
            )
            
            query_obj = session.query(Pin).options(
                joinedload(Pin.creator),
                joinedload(Pin.tags)
            ).filter(
                Pin.is_active == True,
                Pin.is_public == True,
                search_filter
            )
            
            if category:
                query_obj = query_obj.filter(Pin.category == category)
            
            pins = query_obj.order_by(desc(Pin.created_at)).limit(limit).all()
            
            results = [self._serialize_pin(pin) for pin in pins]
            
            self.cache.set(cache_key, json.dumps(results), ttl=1800)
            
            return results
    
    def get_trending_pins(self, limit: int = 10, time_window_hours: int = 24) -> List[Dict]:
        cache_key = CACHE_KEYS['TRENDING']
        
        cached_trending = self.cache.get(cache_key)
        if cached_trending:
            return json.loads(cached_trending)
        
        with db_manager.get_session() as session:
            time_threshold = datetime.now() - timedelta(hours=time_window_hours)
            
            interaction_counts = session.query(
                Interaction.pin_id,
                func.count(Interaction.id).label('interaction_count')
            ).filter(
                Interaction.created_at >= time_threshold
            ).group_by(Interaction.pin_id).subquery()
            
            trending_query = session.query(
                Pin,
                interaction_counts.c.interaction_count,
                func.count(Like.id).label('like_count'),
                func.count(Save.id).label('save_count')
            ).outerjoin(
                interaction_counts,
                Pin.id == interaction_counts.c.pin_id
            ).outerjoin(Like, Pin.id == Like.pin_id)\
             .outerjoin(Save, Pin.id == Save.pin_id)\
             .filter(
                 Pin.is_active == True,
                 Pin.is_public == True
             ).group_by(Pin.id, interaction_counts.c.interaction_count)\
             .order_by(
                 desc(interaction_counts.c.interaction_count),
                 desc(func.count(Like.id)),
                 desc(func.count(Save.id)),
                 desc(Pin.created_at)
             ).limit(limit)
            
            results = []
            for pin_data in trending_query.all():
                pin, interaction_count, like_count, save_count = pin_data
                
                pin_dict = self._serialize_pin(pin)
                pin_dict['trending_score'] = (interaction_count or 0) + (like_count or 0) + (save_count or 0)
                pin_dict['interaction_count'] = interaction_count or 0
                results.append(pin_dict)
            
            self.cache.set(cache_key, json.dumps(results), ttl=900)
            
            return results
    
    def get_pins_by_category(self, category: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        with db_manager.get_session() as session:
            pins = session.query(Pin).options(
                joinedload(Pin.creator),
                joinedload(Pin.tags)
            ).filter(
                Pin.category == category,
                Pin.is_active == True,
                Pin.is_public == True
            ).order_by(desc(Pin.created_at))\
             .limit(limit)\
             .offset(offset)\
             .all()
            
            return [self._serialize_pin(pin) for pin in pins]
    
    def get_pins_by_tag(self, tag_name: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        with db_manager.get_session() as session:
            pins = session.query(Pin).options(
                joinedload(Pin.creator),
                joinedload(Pin.tags)
            ).join(Pin.tags)\
             .filter(
                 Tag.name == tag_name,
                 Pin.is_active == True,
                 Pin.is_public == True
             ).order_by(desc(Pin.created_at))\
             .limit(limit)\
             .offset(offset)\
             .all()
            
            return [self._serialize_pin(pin) for pin in pins]
    
    def create_pin(self, pin_data: Dict) -> Optional[Dict]:
        try:
            with db_manager.get_session() as session:
                pin = Pin(
                    title=pin_data['title'],
                    description=pin_data.get('description', ''),
                    image_url=pin_data['image_url'],
                    link=pin_data.get('link'),
                    creator_id=pin_data['creator_id'],
                    category=pin_data.get('category'),
                    width=pin_data.get('width'),
                    height=pin_data.get('height')
                )
                
                session.add(pin)
                session.flush()
                
                if 'tag_names' in pin_data:
                    tags = session.query(Tag).filter(Tag.name.in_(pin_data['tag_names'])).all()
                    pin.tags.extend(tags)
                
                session.commit()
                
                self._clear_pin_caches(pin.id)
                
                return self.get_pin_by_id(pin.id)
                
        except Exception as e:
            print(f"Error creating pin: {e}")
            return None
    
    def update_pin(self, pin_id: int, pin_data: Dict) -> Optional[Dict]:
        try:
            with db_manager.get_session() as session:
                pin = session.query(Pin).filter(Pin.id == pin_id).first()
                if not pin:
                    return None
                
                for key, value in pin_data.items():
                    if hasattr(pin, key) and key not in ['id', 'creator_id', 'created_at']:
                        setattr(pin, key, value)
                
                pin.updated_at = datetime.now()
                session.commit()
                
                self._clear_pin_caches(pin_id)
                
                return self.get_pin_by_id(pin_id)
                
        except Exception as e:
            print(f"Error updating pin: {e}")
            return None
    
    def delete_pin(self, pin_id: int, user_id: int) -> bool:
        try:
            with db_manager.get_session() as session:
                pin = session.query(Pin).filter(
                    Pin.id == pin_id,
                    Pin.creator_id == user_id
                ).first()
                
                if not pin:
                    return False
                
                pin.is_active = False
                pin.updated_at = datetime.now()
                session.commit()
                
                self._clear_pin_caches(pin_id)
                
                return True
                
        except Exception as e:
            print(f"Error deleting pin: {e}")
            return False
    
    def like_pin(self, pin_id: int, user_id: int) -> bool:
        try:
            with db_manager.get_session() as session:
                existing_like = session.query(Like).filter(
                    Like.user_id == user_id,
                    Like.pin_id == pin_id
                ).first()
                
                if existing_like:
                    return False
                
                like = Like(user_id=user_id, pin_id=pin_id)
                session.add(like)
                session.commit()
                
                self._clear_pin_caches(pin_id)
                
                return True
                
        except Exception as e:
            print(f"Error liking pin: {e}")
            return False
    
    def unlike_pin(self, pin_id: int, user_id: int) -> bool:
        try:
            with db_manager.get_session() as session:
                like = session.query(Like).filter(
                    Like.user_id == user_id,
                    Like.pin_id == pin_id
                ).first()
                
                if not like:
                    return False
                
                session.delete(like)
                session.commit()
                
                self._clear_pin_caches(pin_id)
                
                return True
                
        except Exception as e:
            print(f"Error unliking pin: {e}")
            return False
    
    def save_pin(self, pin_id: int, user_id: int, board_id: int = None) -> bool:
        try:
            with db_manager.get_session() as session:
                existing_save = session.query(Save).filter(
                    Save.user_id == user_id,
                    Save.pin_id == pin_id
                ).first()
                
                if existing_save:
                    return False
                
                save = Save(user_id=user_id, pin_id=pin_id, board_id=board_id)
                session.add(save)
                session.commit()
                
                self._clear_pin_caches(pin_id)
                
                return True
                
        except Exception as e:
            print(f"Error saving pin: {e}")
            return False
    
    def unsave_pin(self, pin_id: int, user_id: int) -> bool:
        try:
            with db_manager.get_session() as session:
                save = session.query(Save).filter(
                    Save.user_id == user_id,
                    Save.pin_id == pin_id
                ).first()
                
                if not save:
                    return False
                
                session.delete(save)
                session.commit()
                
                self._clear_pin_caches(pin_id)
                
                return True
                
        except Exception as e:
            print(f"Error unsaving pin: {e}")
            return False
    
    def record_interaction(self, pin_id: int, user_id: int, interaction_type: str, metadata: Dict = None):
        try:
            with db_manager.get_session() as session:
                interaction = Interaction(
                    user_id=user_id,
                    pin_id=pin_id,
                    interaction_type=interaction_type,
                    metadata=json.dumps(metadata) if metadata else None
                )
                session.add(interaction)
                session.commit()
                
                self.cache.delete(CACHE_KEYS['TRENDING'])
                
        except Exception as e:
            print(f"Error recording interaction: {e}")
    
    def get_pin_stats(self, pin_id: int) -> Dict:
        cache_key = CACHE_KEYS['PIN_STATS'].format(id=pin_id)
        
        cached_stats = self.cache.get(cache_key)
        if cached_stats:
            return json.loads(cached_stats)
        
        with db_manager.get_session() as session:
            pin = session.query(Pin).filter(Pin.id == pin_id).first()
            if not pin:
                return {}
            
            stats = {
                'like_count': pin.like_count,
                'save_count': pin.save_count,
                'comment_count': pin.comment_count,
                'interaction_count': session.query(Interaction).filter(
                    Interaction.pin_id == pin_id
                ).count(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Cache stats for 5 minutes
            self.cache.set(cache_key, json.dumps(stats), ttl=300)
            
            return stats
    
    def _serialize_pin(self, pin: Pin) -> Dict:
        """Serialize pin object to dictionary"""
        pin_dict = pin.to_dict()
        
        # Add creator info
        if pin.creator:
            pin_dict['creator'] = {
                'id': pin.creator.id,
                'username': pin.creator.username,
                'name': pin.creator.name,
                'avatar_url': pin.creator.avatar_url
            }
        
        # Add tags
        if pin.tags:
            pin_dict['tags'] = [tag.to_dict() for tag in pin.tags]
        
        # Add interaction info (for current user would be added in API layer)
        pin_dict['isLiked'] = False
        pin_dict['isSaved'] = False
        
        return pin_dict
    
    def _clear_pin_caches(self, pin_id: int):
        """Clear all caches related to a pin"""
        cache_keys_to_clear = [
            CACHE_KEYS['PIN'].format(id=pin_id),
            CACHE_KEYS['PIN_STATS'].format(id=pin_id),
            CACHE_KEYS['TRENDING']
        ]
        
        for key in cache_keys_to_clear:
            self.cache.delete(key)
        
        # Clear search cache patterns
        self.cache.delete_pattern('search:*')

# Global pin service instance
pin_service = PinService()
