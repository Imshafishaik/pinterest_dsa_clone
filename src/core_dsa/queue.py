"""
Queue & Circular Buffer Implementation for Pinterest Clone
Handles notification delivery pipeline, pin activity logging, and rate limiting
"""

import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from threading import Lock
import heapq

@dataclass
class ActivityLog:
    """Pin activity log entry"""
    pin_id: str
    user_id: str
    action: str  # 'save', 'like', 'comment', 'create'
    timestamp: float
    metadata: Dict = None

@dataclass
class NotificationEvent:
    """Notification event for delivery pipeline"""
    event_id: str
    user_id: str
    event_type: str  # 'new_follower', 'pin_saved', 'board_updated'
    data: Dict
    timestamp: float
    priority: int = 5  # Lower = higher priority
    retry_count: int = 0
    max_retries: int = 3

class CircularBuffer:
    """Circular buffer for sliding window operations"""
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = [None] * capacity
        self.head = 0  # Points to the next write position
        self.tail = 0  # Points to the oldest element
        self.size = 0
        self.lock = Lock()
    
    def append(self, item: Any) -> bool:
        """Add item to buffer, returns True if buffer was full and oldest item was overwritten"""
        with self.lock:
            was_full = self.size == self.capacity
            
            self.buffer[self.head] = item
            self.head = (self.head + 1) % self.capacity
            
            if was_full:
                self.tail = (self.tail + 1) % self.capacity
            else:
                self.size += 1
            
            return was_full
    
    def pop(self) -> Optional[Any]:
        """Remove and return oldest item"""
        with self.lock:
            if self.size == 0:
                return None
            
            item = self.buffer[self.tail]
            self.buffer[self.tail] = None
            self.tail = (self.tail + 1) % self.capacity
            self.size -= 1
            
            return item
    
    def peek(self) -> Optional[Any]:
        """Peek at oldest item without removing"""
        with self.lock:
            if self.size == 0:
                return None
            return self.buffer[self.tail]
    
    def get_items(self) -> List[Any]:
        """Get all items in buffer (oldest to newest)"""
        with self.lock:
            items = []
            for i in range(self.size):
                index = (self.tail + i) % self.capacity
                items.append(self.buffer[index])
            return items
    
    def is_full(self) -> bool:
        """Check if buffer is full"""
        return self.size == self.capacity
    
    def is_empty(self) -> bool:
        """Check if buffer is empty"""
        return self.size == 0
    
    def clear(self) -> None:
        """Clear all items from buffer"""
        with self.lock:
            self.buffer = [None] * self.capacity
            self.head = 0
            self.tail = 0
            self.size = 0

class ActivityLogger:
    """Circular buffer-based activity logger for pins"""
    
    def __init__(self, capacity: int = 10000):
        self.activity_buffer = CircularBuffer(capacity)
        self.pin_activities = {}  # pin_id -> deque of recent activities
        self.user_activities = {}  # user_id -> deque of recent activities
    
    def log_activity(self, pin_id: str, user_id: str, action: str, metadata: Dict = None) -> None:
        """Log pin activity"""
        activity = ActivityLog(
            pin_id=pin_id,
            user_id=user_id,
            action=action,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        # Add to circular buffer
        self.activity_buffer.append(activity)
        
        # Add to pin-specific activities (keep last 100 per pin)
        if pin_id not in self.pin_activities:
            self.pin_activities[pin_id] = deque(maxlen=100)
        self.pin_activities[pin_id].append(activity)
        
        # Add to user-specific activities (keep last 200 per user)
        if user_id not in self.user_activities:
            self.user_activities[user_id] = deque(maxlen=200)
        self.user_activities[user_id].append(activity)
    
    def get_pin_activities(self, pin_id: str, limit: int = 50) -> List[ActivityLog]:
        """Get recent activities for a specific pin"""
        activities = list(self.pin_activities.get(pin_id, []))
        activities.sort(key=lambda x: x.timestamp, reverse=True)
        return activities[:limit]
    
    def get_user_activities(self, user_id: str, limit: int = 50) -> List[ActivityLog]:
        """Get recent activities for a specific user"""
        activities = list(self.user_activities.get(user_id, []))
        activities.sort(key=lambda x: x.timestamp, reverse=True)
        return activities[:limit]
    
    def get_recent_activities(self, limit: int = 100) -> List[ActivityLog]:
        """Get most recent activities across all pins"""
        all_activities = self.activity_buffer.get_items()
        all_activities.sort(key=lambda x: x.timestamp, reverse=True)
        return all_activities[:limit]
    
    def get_activity_stats(self, pin_id: str, time_window_hours: int = 24) -> Dict:
        """Get activity statistics for a pin within time window"""
        activities = self.get_pin_activities(pin_id, limit=1000)
        cutoff_time = time.time() - (time_window_hours * 3600)
        
        recent_activities = [a for a in activities if a.timestamp > cutoff_time]
        
        action_counts = {}
        for activity in recent_activities:
            action_counts[activity.action] = action_counts.get(activity.action, 0) + 1
        
        return {
            'total_activities': len(recent_activities),
            'action_breakdown': action_counts,
            'unique_users': len(set(a.user_id for a in recent_activities)),
            'time_window_hours': time_window_hours
        }

class SlidingWindowRateLimiter:
    """Rate limiter using sliding window algorithm"""
    
    def __init__(self, window_size_seconds: int, max_requests: int):
        self.window_size = window_size_seconds
        self.max_requests = max_requests
        self.client_windows = {}  # client_id -> CircularBuffer
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if client is allowed to make request"""
        current_time = time.time()
        
        if client_id not in self.client_windows:
            self.client_windows[client_id] = CircularBuffer(self.max_requests)
        
        buffer = self.client_windows[client_id]
        
        # Remove old entries outside window
        while not buffer.is_empty():
            oldest = buffer.peek()
            if current_time - oldest > self.window_size:
                buffer.pop()
            else:
                break
        
        # Check if under limit
        if buffer.size < self.max_requests:
            buffer.append(current_time)
            return True
        
        return False
    
    def get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client"""
        if client_id not in self.client_windows:
            return self.max_requests
        
        current_time = time.time()
        buffer = self.client_windows[client_id]
        
        # Remove old entries
        while not buffer.is_empty():
            oldest = buffer.peek()
            if current_time - oldest > self.window_size:
                buffer.pop()
            else:
                break
        
        return max(0, self.max_requests - buffer.size)
    
    def reset_client(self, client_id: str) -> None:
        """Reset rate limit for client"""
        if client_id in self.client_windows:
            del self.client_windows[client_id]

class NotificationPipeline:
    """Priority queue-based notification delivery pipeline"""
    
    def __init__(self, max_queue_size: int = 50000):
        self.max_queue_size = max_queue_size
        self.priority_queue = []  # Min-heap of NotificationEvent
        self.delivery_queue = deque()  # FIFO for actual delivery
        self.failed_events = deque()  # Failed events for retry
        self.processing_events = set()  # Events currently being processed
        self.delivered_events = set()  # Successfully delivered events
        self.lock = Lock()
        
        # Rate limiting for different notification types
        self.rate_limiters = {
            'new_follower': SlidingWindowRateLimiter(3600, 10),  # 10 per hour
            'pin_saved': SlidingWindowRateLimiter(3600, 50),     # 50 per hour
            'board_updated': SlidingWindowRateLimiter(3600, 20), # 20 per hour
            'comment': SlidingWindowRateLimiter(3600, 30)        # 30 per hour
        }
    
    def add_notification(self, event_id: str, user_id: str, event_type: str, 
                       data: Dict, priority: int = 5) -> bool:
        """Add notification to pipeline"""
        # Check rate limits
        rate_limiter = self.rate_limiters.get(event_type)
        if rate_limiter and not rate_limiter.is_allowed(user_id):
            return False  # Rate limited
        
        event = NotificationEvent(
            event_id=event_id,
            user_id=user_id,
            event_type=event_type,
            data=data,
            timestamp=time.time(),
            priority=priority
        )
        
        with self.lock:
            if len(self.priority_queue) >= self.max_queue_size:
                # Remove lowest priority event if new event has higher priority
                if self.priority_queue and priority < self.priority_queue[0].priority:
                    heapq.heappop(self.priority_queue)
                else:
                    return False  # Queue full and can't add
            
            heapq.heappush(self.priority_queue, event)
            return True
    
    def get_next_notification(self) -> Optional[NotificationEvent]:
        """Get next notification for processing"""
        with self.lock:
            # First, try failed events (retry)
            if self.failed_events:
                event = self.failed_events.popleft()
                event.retry_count += 1
                return event
            
            # Then, get from priority queue
            if self.priority_queue:
                event = heapq.heappop(self.priority_queue)
                self.processing_events.add(event.event_id)
                return event
            
            return None
    
    def mark_delivered(self, event_id: str) -> bool:
        """Mark notification as successfully delivered"""
        with self.lock:
            if event_id in self.processing_events:
                self.processing_events.remove(event_id)
                self.delivered_events.add(event_id)
                return True
            return False
    
    def mark_failed(self, event_id: str, permanent: bool = False) -> bool:
        """Mark notification as failed"""
        with self.lock:
            if event_id in self.processing_events:
                self.processing_events.remove(event_id)
                
                # Find the event and check retry count
                for event in self.priority_queue:
                    if event.event_id == event_id:
                        if not permanent and event.retry_count < event.max_retries:
                            # Add to failed queue for retry
                            self.failed_events.append(event)
                        return True
                
                return False
            return False
    
    def get_pending_count(self) -> int:
        """Get count of pending notifications"""
        with self.lock:
            return len(self.priority_queue) + len(self.failed_events)
    
    def get_processing_count(self) -> int:
        """Get count of notifications being processed"""
        with self.lock:
            return len(self.processing_events)
    
    def get_delivered_count(self) -> int:
        """Get count of delivered notifications"""
        with self.lock:
            return len(self.delivered_events)
    
    def cleanup_old_events(self, max_age_hours: int = 24) -> int:
        """Clean up old delivered events"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        with self.lock:
            old_events = []
            for event_id in list(self.delivered_events):
                # This is simplified - in production, store timestamps with events
                old_events.append(event_id)
            
            for event_id in old_events[:1000]:  # Limit cleanup batch size
                self.delivered_events.remove(event_id)
            
            return len(old_events)
    
    def get_pipeline_stats(self) -> Dict:
        """Get pipeline statistics"""
        with self.lock:
            return {
                'pending_notifications': len(self.priority_queue),
                'failed_notifications': len(self.failed_events),
                'processing_notifications': len(self.processing_events),
                'delivered_notifications': len(self.delivered_events),
                'max_queue_size': self.max_queue_size,
                'queue_utilization': (len(self.priority_queue) + len(self.failed_events)) / self.max_queue_size
            }

class PinterestQueueManager:
    """Unified queue management for Pinterest"""
    
    def __init__(self):
        self.activity_logger = ActivityLogger(capacity=50000)
        self.notification_pipeline = NotificationPipeline()
        self.rate_limiters = {
            'api_requests': SlidingWindowRateLimiter(60, 1000),    # 1000 per minute
            'search_requests': SlidingWindowRateLimiter(60, 100),   # 100 per minute
            'upload_requests': SlidingWindowRateLimiter(3600, 50), # 50 per hour
            'follow_requests': SlidingWindowRateLimiter(3600, 100) # 100 per hour
        }
    
    def log_pin_activity(self, pin_id: str, user_id: str, action: str, metadata: Dict = None) -> None:
        """Log pin activity"""
        self.activity_logger.log_activity(pin_id, user_id, action, metadata)
    
    def get_pin_activity_stats(self, pin_id: str) -> Dict:
        """Get activity statistics for pin"""
        return self.activity_logger.get_activity_stats(pin_id)
    
    def add_notification(self, event_id: str, user_id: str, event_type: str, 
                       data: Dict, priority: int = 5) -> bool:
        """Add notification to pipeline"""
        return self.notification_pipeline.add_notification(
            event_id, user_id, event_type, data, priority
        )
    
    def process_notifications(self, batch_size: int = 10) -> List[NotificationEvent]:
        """Process batch of notifications"""
        notifications = []
        
        for _ in range(batch_size):
            notification = self.notification_pipeline.get_next_notification()
            if notification:
                notifications.append(notification)
            else:
                break
        
        return notifications
    
    def check_rate_limit(self, limit_type: str, client_id: str) -> bool:
        """Check if client is rate limited"""
        rate_limiter = self.rate_limiters.get(limit_type)
        if rate_limiter:
            return rate_limiter.is_allowed(client_id)
        return True
    
    def get_remaining_requests(self, limit_type: str, client_id: str) -> int:
        """Get remaining requests for client"""
        rate_limiter = self.rate_limiters.get(limit_type)
        if rate_limiter:
            return rate_limiter.get_remaining_requests(client_id)
        return 0
    
    def get_recent_activities(self, limit: int = 100) -> List[ActivityLog]:
        """Get recent activities"""
        return self.activity_logger.get_recent_activities(limit)
    
    def get_user_activities(self, user_id: str, limit: int = 50) -> List[ActivityLog]:
        """Get user activities"""
        return self.activity_logger.get_user_activities(user_id, limit)
    
    def cleanup_old_data(self) -> Dict[str, int]:
        """Clean up old data"""
        return {
            'old_notifications_cleaned': self.notification_pipeline.cleanup_old_events(),
            'old_activities_cleaned': len(self.activity_logger.activity_buffer.get_items()) - 10000  # Keep last 10k
        }
    
    def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        return {
            'activity_logger': {
                'buffer_size': self.activity_logger.activity_buffer.size,
                'buffer_capacity': self.activity_logger.activity_buffer.capacity,
                'tracked_pins': len(self.activity_logger.pin_activities),
                'tracked_users': len(self.activity_logger.user_activities)
            },
            'notification_pipeline': self.notification_pipeline.get_pipeline_stats(),
            'rate_limiters': {
                name: {
                    'active_clients': len(limiter.client_windows),
                    'window_size': limiter.window_size,
                    'max_requests': limiter.max_requests
                }
                for name, limiter in self.rate_limiters.items()
            }
        }
