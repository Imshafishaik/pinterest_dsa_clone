"""
Smart Feed Ranking Feature for Pinterest Clone
Implements O(n log k) k-way merge algorithm for personalized feed ranking
"""

import time
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from core_dsa.priority_queue import FeedRankingQueue, PinterestPriorityManager
from core_dsa.graph import PinterestGraph
from core_dsa.hash_map import PinterestCacheManager

@dataclass
class FeedItem:
    """Feed item with ranking metadata"""
    pin_id: str
    score: float
    relevance_factors: Dict
    timestamp: float
    
class SmartFeedRanking:
    """Smart feed ranking algorithm using priority queue and k-way merge"""
    
    def __init__(self, graph: PinterestGraph, cache_manager: PinterestCacheManager):
        self.graph = graph
        self.cache_manager = cache_manager
        self.feed_queue = FeedRankingQueue(max_size=10000)
        
        # Scoring weights
        self.weights = {
            'engagement': 0.4,
            'recency': 0.2,
            'user_affinity': 0.25,
            'board_affinity': 0.15
        }
    
    def calculate_engagement_score(self, pin_data: Dict) -> float:
        """Calculate engagement score based on likes, saves, comments"""
        likes = pin_data.get('likes', 0)
        saves = pin_data.get('saves', 0)
        comments = pin_data.get('comments', 0)
        
        # Weighted engagement formula
        engagement = (likes * 1.0) + (saves * 2.0) + (comments * 1.5)
        
        # Apply logarithmic scaling to prevent domination
        return min(engagement / 100.0, 10.0)
    
    def calculate_recency_score(self, pin_data: Dict) -> float:
        """Calculate recency score (newer pins get higher scores)"""
        created_at = pin_data.get('created_at', time.time())
        
        if isinstance(created_at, str):
            created_at = time.time()  # Fallback for string timestamps
        
        hours_old = (time.time() - created_at) / 3600
        
        # Exponential decay: newer pins get exponentially higher scores
        if hours_old < 1:
            return 1.0
        elif hours_old < 24:
            return 0.8
        elif hours_old < 168:  # 1 week
            return 0.5
        else:
            return 0.2
    
    def calculate_user_affinity(self, user_id: str, pin_data: Dict) -> float:
        """Calculate user affinity based on interests and social connections"""
        pin_id = pin_data.get('pin_id', '')
        
        # Get user's saved pins
        user_pins = self.graph.get_user_pins(user_id)
        
        # Check if user follows pin creator
        creator_id = pin_data.get('creator_id', '')
        follows_creator = creator_id in self.graph.get_following(user_id)
        
        # Calculate similarity with user's existing pins
        affinity_score = 0.0
        
        if user_pins:
            # Find similar pins through interest graph
            similar_count = 0
            for user_pin in user_pins[:20]:  # Check last 20 pins
                similar_pins = self.graph.bfs_find_similar_pins(user_pin, max_depth=2)
                if pin_id in similar_pins:
                    similar_count += 1
            
            affinity_score = similar_count / min(len(user_pins), 20)
        
        # Boost for following creator
        if follows_creator:
            affinity_score += 0.3
        
        return min(affinity_score, 1.0)
    
    def calculate_board_affinity(self, user_id: str, pin_data: Dict) -> float:
        """Calculate affinity based on user's board preferences"""
        pin_boards = pin_data.get('boards', [])
        
        if not pin_boards:
            return 0.0
        
        # Get user's boards
        user_interests = self.graph.dfs_explore_interests(user_id, max_depth=2)
        user_board_ids = [board.split('_')[-1] for board in user_interests.get('boards', [])]
        
        # Calculate overlap
        overlap = 0
        for pin_board in pin_boards:
            if any(pin_board in user_board for user_board in user_board_ids):
                overlap += 1
        
        return min(overlap / len(pin_boards), 1.0) if pin_boards else 0.0
    
    def calculate_composite_score(self, user_id: str, pin_data: Dict) -> float:
        """Calculate composite ranking score for a pin"""
        engagement_score = self.calculate_engagement_score(pin_data)
        recency_score = self.calculate_recency_score(pin_data)
        user_affinity = self.calculate_user_affinity(user_id, pin_data)
        board_affinity = self.calculate_board_affinity(user_id, pin_data)
        
        # Weighted composite score
        composite_score = (
            engagement_score * self.weights['engagement'] +
            recency_score * self.weights['recency'] +
            user_affinity * self.weights['user_affinity'] +
            board_affinity * self.weights['board_affinity']
        )
        
        # Add small random factor for diversity
        composite_score += random.random() * 0.1
        
        return composite_score
    
    def update_feed_for_pin(self, pin_data: Dict) -> None:
        """Update feed ranking queue for a new pin"""
        pin_id = pin_data.get('pin_id', '')
        
        # Calculate base engagement score
        engagement_score = self.calculate_engagement_score(pin_data)
        
        # Add to feed queue
        self.feed_queue.add_pin(pin_id, pin_data, engagement_score)
        
        # Cache the pin data
        self.cache_manager.cache_pin(pin_id, pin_data, ttl=3600)
    
    def generate_user_feed(self, user_id: str, feed_size: int = 20) -> List[Dict]:
        """Generate personalized feed for user using k-way merge"""
        # Get user preferences for personalization
        user_preferences = self._get_user_preferences(user_id)
        self.feed_queue.update_user_preferences(user_id, user_preferences)
        
        # Get top pins from feed queue
        top_pins = self.feed_queue.get_top_pins(user_id, feed_size * 2)  # Get more for diversity
        
        # Score and rank pins for this specific user
        scored_pins = []
        for pin_data in top_pins:
            composite_score = self.calculate_composite_score(user_id, pin_data)
            
            feed_item = FeedItem(
                pin_id=pin_data.get('pin_id', ''),
                score=composite_score,
                relevance_factors={
                    'engagement': self.calculate_engagement_score(pin_data),
                    'recency': self.calculate_recency_score(pin_data),
                    'user_affinity': self.calculate_user_affinity(user_id, pin_data),
                    'board_affinity': self.calculate_board_affinity(user_id, pin_data)
                },
                timestamp=pin_data.get('created_at', time.time())
            )
            scored_pins.append(feed_item)
        
        # Sort by composite score
        scored_pins.sort(key=lambda x: x.score, reverse=True)
        
        # Convert to feed format
        feed = []
        for item in scored_pins[:feed_size]:
            pin_data = self.cache_manager.get_cached_pin(item.pin_id)
            if pin_data:
                feed_item = {
                    'pin_id': item.pin_id,
                    'pin_data': pin_data,
                    'ranking_score': item.score,
                    'relevance_factors': item.relevance_factors
                }
                feed.append(feed_item)
        
        return feed
    
    def _get_user_preferences(self, user_id: str) -> Dict:
        """Get user preferences for personalization"""
        # Explore user's interests
        interests = self.graph.dfs_explore_interests(user_id, max_depth=2)
        
        preferences = {
            'interests': interests.get('pins', []),
            'boards': interests.get('boards', []),
            'social_connections': len(self.graph.get_following(user_id))
        }
        
        return preferences
    
    def refresh_feed_scores(self, user_id: str) -> None:
        """Refresh feed scores based on updated user activity"""
        # This would be called when user interacts with feed
        user_preferences = self._get_user_preferences(user_id)
        self.feed_queue.update_user_preferences(user_id, user_preferences)
    
    def get_feed_diversity_metrics(self, feed: List[Dict]) -> Dict:
        """Calculate diversity metrics for generated feed"""
        if not feed:
            return {'diversity_score': 0.0, 'categories': {}}
        
        # Analyze creator diversity
        creators = set()
        categories = {}
        time_spread = []
        
        for item in feed:
            pin_data = item.get('pin_data', {})
            creators.add(pin_data.get('creator_id', ''))
            
            # Category analysis (simplified)
            category = pin_data.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
            
            # Time spread
            created_at = pin_data.get('created_at', time.time())
            time_spread.append(created_at)
        
        # Calculate diversity metrics
        creator_diversity = len(creators) / len(feed) if feed else 0
        category_diversity = len(categories) / len(feed) if feed else 0
        
        # Time diversity (spread over hours)
        if time_spread:
            time_range = max(time_spread) - min(time_spread)
            time_diversity = min(time_range / (24 * 3600), 1.0)  # Normalize to 0-1
        else:
            time_diversity = 0.0
        
        overall_diversity = (creator_diversity + category_diversity + time_diversity) / 3
        
        return {
            'diversity_score': overall_diversity,
            'creator_diversity': creator_diversity,
            'category_diversity': category_diversity,
            'time_diversity': time_diversity,
            'categories': categories
        }
    
    def get_ranking_stats(self) -> Dict:
        """Get feed ranking statistics"""
        return {
            'feed_queue_stats': self.feed_queue.get_stats(),
            'cache_stats': self.cache_manager.get_stats(),
            'scoring_weights': self.weights
        }

class FeedPerformanceMonitor:
    """Monitor feed ranking performance and quality"""
    
    def __init__(self):
        self.feed_generations = []
        self.user_interactions = {}
        self.performance_metrics = {
            'avg_generation_time': 0.0,
            'avg_feed_size': 0.0,
            'diversity_scores': []
        }
    
    def record_feed_generation(self, user_id: str, feed: List[Dict], generation_time: float) -> None:
        """Record feed generation metrics"""
        self.feed_generations.append({
            'user_id': user_id,
            'feed_size': len(feed),
            'generation_time': generation_time,
            'timestamp': time.time()
        })
        
        # Update performance metrics
        if self.feed_generations:
            avg_time = sum(g['generation_time'] for g in self.feed_generations[-100:]) / len(self.feed_generations[-100:])
            avg_size = sum(g['feed_size'] for g in self.feed_generations[-100:]) / len(self.feed_generations[-100:])
            
            self.performance_metrics['avg_generation_time'] = avg_time
            self.performance_metrics['avg_feed_size'] = avg_size
    
    def record_user_interaction(self, user_id: str, pin_id: str, interaction_type: str) -> None:
        """Record user interaction with feed items"""
        if user_id not in self.user_interactions:
            self.user_interactions[user_id] = []
        
        self.user_interactions[user_id].append({
            'pin_id': pin_id,
            'interaction_type': interaction_type,
            'timestamp': time.time()
        })
    
    def calculate_engagement_rate(self, user_id: str) -> float:
        """Calculate engagement rate for user"""
        if user_id not in self.user_interactions:
            return 0.0
        
        interactions = self.user_interactions[user_id]
        
        # Count different interaction types
        saves = sum(1 for i in interactions if i['interaction_type'] == 'save')
        likes = sum(1 for i in interactions if i['interaction_type'] == 'like')
        clicks = sum(1 for i in interactions if i['interaction_type'] == 'click')
        
        # Calculate engagement rate (interactions per feed view)
        total_interactions = saves + likes + clicks
        feed_views = len([g for g in self.feed_generations if g['user_id'] == user_id])
        
        if feed_views == 0:
            return 0.0
        
        return total_interactions / feed_views
    
    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report"""
        return {
            'performance_metrics': self.performance_metrics,
            'total_feed_generations': len(self.feed_generations),
            'active_users': len(self.user_interactions),
            'avg_engagement_rate': sum(self.calculate_engagement_rate(uid) for uid in self.user_interactions.keys()) / len(self.user_interactions) if self.user_interactions else 0.0
        }
