import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from threading import Lock
import heapq

@dataclass
class ActivityLog:
    pin_id: str
    user_id: str
    action: str
    timestamp: float
    metadata: Dict = None

@dataclass
class NotificationEvent:
    event_id: str
    user_id: str
    event_type: str
    data: Dict
    timestamp: float
    priority: int = 5
    retry_count: int = 0
    max_retries: int = 3

class CircularBuffer:
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = [None] * capacity
        self.head = 0
        self.size = 0
        self.lock = Lock()
    
    def append(self, item: Any) -> bool:
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
        with self.lock:
            if self.size == 0:
                return None
            
            item = self.buffer[self.tail]
            self.buffer[self.tail] = None
            self.tail = (self.tail + 1) % self.capacity
            self.size -= 1
            
            return item
    
    def peek(self) -> Optional[Any]:
        with self.lock:
            if self.size == 0:
                return None
            return self.buffer[self.tail]
    
    def get_items(self) -> List[Any]:
        with self.lock:
            items = []
            for i in range(self.size):
                index = (self.tail + i) % self.capacity
                items.append(self.buffer[index])
            return items
    
    def is_full(self) -> bool:
        return self.size == self.capacity
    
    def is_empty(self) -> bool:
        return self.size == 0
    
    def clear(self) -> None:
        with self.lock:
            self.buffer = [None] * self.capacity
            self.head = 0
            self.tail = 0
            self.size = 0

class ActivityLogger:
    
    def __init__(self, capacity: int = 10000):
        self.activity_buffer = CircularBuffer(capacity)
        self.pin_activities = {}
    
    def log_activity(self, pin_id: str, user_id: str, action: str, metadata: Dict = None) -> None:
        activity = ActivityLog(
            pin_id=pin_id,
            user_id=user_id,
            action=action,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        self.activity_buffer.append(activity)
        
        if pin_id not in self.pin_activities:
            self.pin_activities[pin_id] = deque(maxlen=100)
        self.pin_activities[pin_id].append(activity)
        
        if user_id not in self.user_activities:
            self.user_activities[user_id] = deque(maxlen=200)
        self.user_activities[user_id].append(activity)
    
    def get_pin_activities(self, pin_id: str, limit: int = 50) -> List[ActivityLog]:
        activities = list(self.pin_activities.get(pin_id, []))
        activities.sort(key=lambda x: x.timestamp, reverse=True)
        return activities[:limit]
    
    def get_user_activities(self, user_id: str, limit: int = 50) -> List[ActivityLog]:
        activities = list(self.user_activities.get(user_id, []))
        activities.sort(key=lambda x: x.timestamp, reverse=True)
        return activities[:limit]
    
    def get_recent_activities(self, limit: int = 100) -> List[ActivityLog]:
        all_activities = self.activity_buffer.get_items()
        all_activities.sort(key=lambda x: x.timestamp, reverse=True)
        return all_activities[:limit]
    
    def get_activity_stats(self, pin_id: str, time_window_hours: int = 24) -> Dict:
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
    
    def __init__(self, window_size_seconds: int, max_requests: int):
        self.window_size = window_size_seconds
        self.max_requests = max_requests
        self.client_windows = {}
    
    def is_allowed(self, client_id: str) -> bool:
        current_time = time.time()
        
        if client_id not in self.client_windows:
            self.client_windows[client_id] = CircularBuffer(self.max_requests)
        
        buffer = self.client_windows[client_id]
        
        while not buffer.is_empty():
            oldest = buffer.peek()
            if current_time - oldest > self.window_size:
                buffer.pop()
            else:
                break
        
        if buffer.size < self.max_requests:
            buffer.append(current_time)
            return True
        
        return False
    
    def get_remaining_requests(self, client_id: str) -> int:
        if client_id not in self.client_windows:
            return self.max_requests
        
        current_time = time.time()
        buffer = self.client_windows[client_id]
        
        while not buffer.is_empty():
            oldest = buffer.peek()
            if current_time - oldest > self.window_size:
                buffer.pop()
            else:
                break
        
        return max(0, self.max_requests - buffer.size)
    
    def reset_client(self, client_id: str) -> None:
        if client_id in self.client_windows:
            del self.client_windows[client_id]

class NotificationPipeline:
    
    def __init__(self, max_queue_size: int = 50000):
        self.max_queue_size = max_queue_size
        self.priority_queue = []
        self.delivery_queue = deque()
        self.failed_events = deque()
        self.processing_events = set()
        self.delivered_events = set()
        self.lock = Lock()
        
        self.rate_limiters = {
            'new_follower': SlidingWindowRateLimiter(3600, 10),
            'pin_saved': SlidingWindowRateLimiter(3600, 50),
            'board_updated': SlidingWindowRateLimiter(3600, 20),
            'comment': SlidingWindowRateLimiter(3600, 30)
        }
    
    def add_notification(self, event_id: str, user_id: str, event_type: str, 
                       data: Dict, priority: int = 5) -> bool:
        """Add notification to pipeline"""
        rate_limiter = self.rate_limiters.get(event_type)
        if rate_limiter and not rate_limiter.is_allowed(user_id):
            return False
        
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
                if self.priority_queue and priority < self.priority_queue[0].priority:
                    heapq.heappop(self.priority_queue)
                else:
                    return False
            
            heapq.heappush(self.priority_queue, event)
            return True
    
    def get_next_notification(self) -> Optional[NotificationEvent]:
        with self.lock:
            if self.failed_events:
                event = self.failed_events.popleft()
                event.retry_count += 1
                return event
            
            if self.priority_queue:
                event = heapq.heappop(self.priority_queue)
                self.processing_events.add(event.event_id)
                return event
            
            return None
    
    def mark_delivered(self, event_id: str) -> bool:
        with self.lock:
            if event_id in self.processing_events:
                self.processing_events.remove(event_id)
                self.delivered_events.add(event_id)
                return True
            return False
    
    def mark_failed(self, event_id: str, permanent: bool = False) -> bool:
        with self.lock:
            if event_id in self.processing_events:
                self.processing_events.remove(event_id)
                
                for event in self.priority_queue:
                    if event.event_id == event_id:
                        if not permanent and event.retry_count < event.max_retries:
                            self.failed_events.append(event)
                        return True
                
                return False
            return False
    
    def get_pending_count(self) -> int:
        with self.lock:
            return len(self.priority_queue) + len(self.failed_events)
    
    def get_processing_count(self) -> int:
        with self.lock:
            return len(self.processing_events)
    
    def get_delivered_count(self) -> int:
        with self.lock:
            return len(self.delivered_events)
    
    def cleanup_old_events(self, max_age_hours: int = 24) -> int:
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        with self.lock:
            old_events = []
            for event_id in list(self.delivered_events):
                old_events.append(event_id)
            
            for event_id in old_events[:1000]:
                self.delivered_events.remove(event_id)
            
            return len(old_events)
    
    def get_pipeline_stats(self) -> Dict:
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
    
    def __init__(self):
        self.activity_logger = ActivityLogger(capacity=50000)
        self.notification_pipeline = NotificationPipeline()
        self.rate_limiters = {
            'api_requests': SlidingWindowRateLimiter(60, 1000),
            'search_requests': SlidingWindowRateLimiter(60, 100),
            'upload_requests': SlidingWindowRateLimiter(3600, 50),
            'follow_requests': SlidingWindowRateLimiter(3600, 100)
        }
    
    def log_pin_activity(self, pin_id: str, user_id: str, action: str, metadata: Dict = None) -> None:
        self.activity_logger.log_activity(pin_id, user_id, action, metadata)
    
    def get_pin_activity_stats(self, pin_id: str) -> Dict:
        return self.activity_logger.get_activity_stats(pin_id)
    
    def add_notification(self, event_id: str, user_id: str, event_type: str, 
                       data: Dict, priority: int = 5) -> bool:
        """Add notification to pipeline"""
        return self.notification_pipeline.add_notification(
            event_id, user_id, event_type, data, priority
        )
    
    def process_notifications(self, batch_size: int = 10) -> List[NotificationEvent]:
        notifications = []
        
        for _ in range(batch_size):
            notification = self.notification_pipeline.get_next_notification()
            if notification:
                notifications.append(notification)
            else:
                break
        
        return notifications
    
    def check_rate_limit(self, limit_type: str, client_id: str) -> bool:
        rate_limiter = self.rate_limiters.get(limit_type)
        if rate_limiter:
            return rate_limiter.is_allowed(client_id)
        return True
    
    def get_remaining_requests(self, limit_type: str, client_id: str) -> int:
        rate_limiter = self.rate_limiters.get(limit_type)
        if rate_limiter:
            return rate_limiter.get_remaining_requests(client_id)
        return 0
    
    def get_recent_activities(self, limit: int = 100) -> List[ActivityLog]:
        return self.activity_logger.get_recent_activities(limit)
    
    def get_user_activities(self, user_id: str, limit: int = 50) -> List[ActivityLog]:
        return self.activity_logger.get_user_activities(user_id, limit)
    
    def cleanup_old_data(self) -> Dict[str, int]:
        return {
            'old_notifications_cleaned': self.notification_pipeline.cleanup_old_events(),
            'old_activities_cleaned': len(self.activity_logger.activity_buffer.get_items()) - 10000
        }
    
    def get_system_stats(self) -> Dict:
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
