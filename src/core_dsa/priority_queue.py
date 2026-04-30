"""
Priority Queue / Heap Implementation for Pinterest Clone
Handles feed ranking, trending Pins, notification management, and top-K retrieval
"""

import heapq
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import random

@dataclass
class PinScore:
    """Pin with engagement score for ranking"""
    pin_id: str
    score: float
    timestamp: float = field(default_factory=time.time)
    
    def __lt__(self, other):
        # Higher score = higher priority (min-heap, so invert comparison)
        return self.score > other.score

@dataclass
class TrendingPin:
    """Trending pin with interaction metrics"""
    pin_id: str
    interaction_count: int
    velocity: float  # interactions per hour
    timestamp: float = field(default_factory=time.time)
    
    def __lt__(self, other):
        # Higher velocity = higher priority
        return self.velocity > other.velocity

@dataclass
class Notification:
    """Notification with priority and timestamp"""
    notification_id: str
    user_id: str
    content: str
    priority: int  # Lower number = higher priority
    timestamp: float = field(default_factory=time.time)
    
    def __lt__(self, other):
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.timestamp < other.timestamp

class FeedRankingQueue:
    """Priority queue for smart feed ranking"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.heap = []  # Min-heap of PinScore objects
        self.pin_data = {}  # pin_id -> pin metadata
        self.user_scores = {}  # user_id -> personalization weights
        
    def add_pin(self, pin_id: str, pin_data: Dict, engagement_score: float) -> bool:
        """Add pin to feed ranking queue"""
        if len(self.heap) >= self.max_size:
            # Remove lowest scoring pin if new pin has higher score
            if self.heap and engagement_score > self.heap[0].score:
                removed = heapq.heappop(self.heap)
                del self.pin_data[removed.pin_id]
            else:
                return False  # Don't add if score is too low
        
        pin_score = PinScore(pin_id, engagement_score)
        heapq.heappush(self.heap, pin_score)
        self.pin_data[pin_id] = pin_data
        return True
    
    def get_top_pins(self, user_id: str, k: int = 10) -> List[Dict]:
        """Get top-k pins for user feed with personalization"""
        # Create a copy of heap for processing
        temp_heap = self.heap.copy()
        scored_pins = []
        
        while temp_heap and len(scored_pins) < k:
            pin_score = heapq.heappop(temp_heap)
            pin_data = self.pin_data[pin_score.pin_id].copy()
            
            # Apply personalization
            personalized_score = self._personalize_score(pin_score, user_id)
            pin_data['personalized_score'] = personalized_score
            scored_pins.append(pin_data)
        
        # Sort by personalized score
        scored_pins.sort(key=lambda x: x['personalized_score'], reverse=True)
        return scored_pins[:k]
    
    def _personalize_score(self, pin_score: PinScore, user_id: str) -> float:
        """Apply personalization based on user preferences"""
        base_score = pin_score.score
        user_weight = self.user_scores.get(user_id, 1.0)
        
        # Apply time decay (newer pins get boost)
        time_factor = 1.0 + (time.time() - pin_score.timestamp) / 3600 * 0.1
        
        return base_score * user_weight * time_factor
    
    def update_user_preferences(self, user_id: str, preferences: Dict) -> None:
        """Update user personalization weights"""
        # Simple preference scoring based on interests
        weight = 1.0
        if preferences.get('interests'):
            weight += len(preferences['interests']) * 0.1
        if preferences.get('boards'):
            weight += len(preferences['boards']) * 0.05
        
        self.user_scores[user_id] = min(weight, 3.0)  # Cap at 3x
    
    def remove_pin(self, pin_id: str) -> bool:
        """Remove pin from queue"""
        # This is O(n) - in production, use a more efficient data structure
        for i, pin_score in enumerate(self.heap):
            if pin_score.pin_id == pin_id:
                self.heap.pop(i)
                heapq.heapify(self.heap)
                del self.pin_data[pin_id]
                return True
        return False
    
    def get_stats(self) -> Dict:
        """Get queue statistics"""
        return {
            'size': len(self.heap),
            'max_size': self.max_size,
            'utilization': len(self.heap) / self.max_size,
            'avg_score': sum(ps.score for ps in self.heap) / len(self.heap) if self.heap else 0
        }

class TrendingDetector:
    """Min-heap for maintaining top-K trending pins"""
    
    def __init__(self, k: int = 100, window_hours: int = 24):
        self.k = k
        self.window_hours = window_hours
        self.heap = []  # Min-heap of TrendingPin objects
        self.interaction_history = defaultdict(list)  # pin_id -> [timestamp, ...]
        self.current_time = time.time()
        
    def record_interaction(self, pin_id: str) -> None:
        """Record a pin interaction"""
        timestamp = time.time()
        self.interaction_history[pin_id].append(timestamp)
        
        # Clean old interactions outside window
        cutoff_time = timestamp - (self.window_hours * 3600)
        self.interaction_history[pin_id] = [
            ts for ts in self.interaction_history[pin_id] if ts > cutoff_time
        ]
        
        # Update trending status
        self._update_trending_status(pin_id)
    
    def _update_trending_status(self, pin_id: str) -> None:
        """Update pin's trending status"""
        interactions = self.interaction_history[pin_id]
        if not interactions:
            return
        
        # Calculate velocity (interactions per hour)
        time_span = (interactions[-1] - interactions[0]) / 3600  # hours
        time_span = max(time_span, 1)  # Avoid division by zero
        velocity = len(interactions) / time_span
        
        trending_pin = TrendingPin(pin_id, len(interactions), velocity)
        
        # Check if pin is already in heap
        for i, pin in enumerate(self.heap):
            if pin.pin_id == pin_id:
                # Update existing entry
                self.heap[i] = trending_pin
                heapq.heapify(self.heap)
                return
        
        # Add new pin if it qualifies
        if len(self.heap) < self.k:
            heapq.heappush(self.heap, trending_pin)
        elif velocity > self.heap[0].velocity:
            # Replace lowest velocity pin
            heapq.heappop(self.heap)
            heapq.heappush(self.heap, trending_pin)
    
    def get_trending_pins(self, limit: int = 50) -> List[Dict]:
        """Get top trending pins"""
        # Sort by velocity descending
        sorted_pins = sorted(self.heap, key=lambda x: x.velocity, reverse=True)
        
        return [
            {
                'pin_id': pin.pin_id,
                'interaction_count': pin.interaction_count,
                'velocity': pin.velocity,
                'timestamp': pin.timestamp
            }
            for pin in sorted_pins[:limit]
        ]
    
    def cleanup_old_data(self) -> int:
        """Clean up interaction history outside window"""
        current_time = time.time()
        cutoff_time = current_time - (self.window_hours * 3600)
        
        removed_count = 0
        for pin_id in list(self.interaction_history.keys()):
            old_interactions = [
                ts for ts in self.interaction_history[pin_id] if ts <= cutoff_time
            ]
            if old_interactions:
                self.interaction_history[pin_id] = [
                    ts for ts in self.interaction_history[pin_id] if ts > cutoff_time
                ]
                removed_count += len(old_interactions)
                
                # Remove pin from trending if no recent interactions
                if not self.interaction_history[pin_id]:
                    self._remove_from_trending(pin_id)
                    del self.interaction_history[pin_id]
        
        return removed_count
    
    def _remove_from_trending(self, pin_id: str) -> None:
        """Remove pin from trending heap"""
        for i, pin in enumerate(self.heap):
            if pin.pin_id == pin_id:
                self.heap.pop(i)
                heapq.heapify(self.heap)
                break

class NotificationQueue:
    """Priority queue for notification management"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.heap = []  # Min-heap of Notification objects
        self.user_queues = defaultdict(list)  # user_id -> [notification_id, ...]
        self.notification_data = {}  # notification_id -> Notification
        
    def add_notification(self, notification_id: str, user_id: str, 
                         content: str, priority: int = 5) -> bool:
        """Add notification to queue"""
        if len(self.heap) >= self.max_size:
            # Remove lowest priority notification
            if self.heap:
                removed = heapq.heappop(self.heap)
                self._cleanup_notification(removed.notification_id)
            else:
                return False
        
        notification = Notification(notification_id, user_id, content, priority)
        heapq.heappush(self.heap, notification)
        self.user_queues[user_id].append(notification_id)
        self.notification_data[notification_id] = notification
        return True
    
    def get_user_notifications(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get notifications for a specific user"""
        user_notification_ids = self.user_queues[user_id]
        notifications = []
        
        for notif_id in user_notification_ids[-limit:]:  # Get most recent
            notif = self.notification_data.get(notif_id)
            if notif:
                notifications.append({
                    'id': notif.notification_id,
                    'content': notif.content,
                    'priority': notif.priority,
                    'timestamp': notif.timestamp
                })
        
        # Sort by priority and timestamp
        notifications.sort(key=lambda x: (x['priority'], x['timestamp']))
        return notifications
    
    def mark_delivered(self, notification_id: str) -> bool:
        """Mark notification as delivered and remove from queue"""
        return self._cleanup_notification(notification_id)
    
    def _cleanup_notification(self, notification_id: str) -> bool:
        """Remove notification from all data structures"""
        if notification_id not in self.notification_data:
            return False
        
        notification = self.notification_data[notification_id]
        user_id = notification.user_id
        
        # Remove from heap (O(n) operation)
        for i, notif in enumerate(self.heap):
            if notif.notification_id == notification_id:
                self.heap.pop(i)
                heapq.heapify(self.heap)
                break
        
        # Remove from user queue
        if notification_id in self.user_queues[user_id]:
            self.user_queues[user_id].remove(notification_id)
        
        # Remove from data
        del self.notification_data[notification_id]
        return True
    
    def get_queue_stats(self) -> Dict:
        """Get notification queue statistics"""
        return {
            'total_notifications': len(self.heap),
            'max_size': self.max_size,
            'users_with_notifications': len(self.user_queues),
            'avg_priority': sum(n.priority for n in self.heap) / len(self.heap) if self.heap else 0
        }

class KWayMerge:
    """K-way merge algorithm for combining multiple sorted lists"""
    
    @staticmethod
    def merge_k_sorted_lists(lists: List[List[Tuple[Any, float]]], k: int = 10) -> List[Tuple[Any, float]]:
        """
        Merge k sorted lists by score using min-heap
        Each list should be sorted in descending order by score
        """
        min_heap = []
        result = []
        
        # Initialize heap with first element from each list
        for i, lst in enumerate(lists):
            if lst:
                item, score = lst[0]
                heapq.heappush(min_heap, (-score, i, 0, item))  # Negative for max-heap behavior
        
        # Extract and merge
        while min_heap and len(result) < k:
            neg_score, list_idx, item_idx, item = heapq.heappop(min_heap)
            result.append((item, -neg_score))
            
            # Add next element from the same list
            next_idx = item_idx + 1
            if next_idx < len(lists[list_idx]):
                next_item, next_score = lists[list_idx][next_idx]
                heapq.heappush(min_heap, (-next_score, list_idx, next_idx, next_item))
        
        return result

class PinterestPriorityManager:
    """Unified priority queue management for Pinterest"""
    
    def __init__(self):
        self.feed_queue = FeedRankingQueue(max_size=5000)
        self.trending_detector = TrendingDetector(k=100)
        self.notification_queue = NotificationQueue(max_size=20000)
        self.k_way_merger = KWayMerge()
    
    def rank_feed_pins(self, user_id: str, k: int = 10) -> List[Dict]:
        """Get ranked feed pins for user"""
        return self.feed_queue.get_top_pins(user_id, k)
    
    def get_trending_content(self, limit: int = 50) -> List[Dict]:
        """Get trending pins"""
        return self.trending_detector.get_trending_pins(limit)
    
    def deliver_notifications(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get notifications for user"""
        return self.notification_queue.get_user_notifications(user_id, limit)
    
    def record_pin_interaction(self, pin_id: str) -> None:
        """Record pin interaction for trending detection"""
        self.trending_detector.record_interaction(pin_id)
    
    def add_notification(self, notification_id: str, user_id: str, 
                        content: str, priority: int = 5) -> bool:
        """Add notification"""
        return self.notification_queue.add_notification(notification_id, user_id, content, priority)
    
    def merge_multiple_feeds(self, user_feeds: Dict[str, List], k: int = 10) -> List[Dict]:
        """Merge multiple user feeds using k-way merge"""
        # Convert to list format for k-way merge
        feed_lists = []
        for feed_name, pins in user_feeds.items():
            scored_pins = [(pin, pin.get('score', 0)) for pin in pins]
            scored_pins.sort(key=lambda x: x[1], reverse=True)
            feed_lists.append(scored_pins)
        
        merged = self.k_way_merger.merge_k_sorted_lists(feed_lists, k)
        
        # Convert back to pin format
        return [item for item, score in merged]
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired data across all queues"""
        return {
            'trending_interactions_cleaned': self.trending_detector.cleanup_old_data(),
            'notifications_delivered': len([n for n in self.notification_queue.heap 
                                          if time.time() - n.timestamp > 86400])  # 24h old
        }
    
    def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        return {
            'feed_ranking': self.feed_queue.get_stats(),
            'trending_detection': {
                'trending_pins': len(self.trending_detector.heap),
                'tracked_pins': len(self.trending_detector.interaction_history)
            },
            'notifications': self.notification_queue.get_queue_stats()
        }
