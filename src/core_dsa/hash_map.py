import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple
from collections import OrderedDict
import time
import bisect

class PinterestHashMap:
    
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.size = 0
        self.buckets = [[] for _ in range(capacity)]
        self.load_factor = 0.75
        
    def _hash(self, key: str) -> int:
        return hash(key) % self.capacity
    
    def put(self, key: str, value: Any) -> bool:
        if self.size >= self.capacity * self.load_factor:
            self._resize()
        
        bucket_index = self._hash(key)
        bucket = self.buckets[bucket_index]
        
        for i, (k, v) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return True
        
        bucket.append((key, value))
        self.size += 1
        return True
    
    def get(self, key: str) -> Optional[Any]:
        bucket_index = self._hash(key)
        bucket = self.buckets[bucket_index]
        
        for k, v in bucket:
            if k == key:
                return v
        return None
    
    def remove(self, key: str) -> bool:
        bucket_index = self._hash(key)
        bucket = self.buckets[bucket_index]
        
        for i, (k, v) in enumerate(bucket):
            if k == key:
                bucket.pop(i)
                self.size -= 1
                return True
        return False
    
    def _resize(self):
        new_capacity = self.capacity * 2
        new_buckets = [[] for _ in range(new_capacity)]
        
        for bucket in self.buckets:
            for key, value in bucket:
                new_index = hash(key) % new_capacity
                new_buckets[new_index].append((key, value))
        
        self.capacity = new_capacity
        self.buckets = new_buckets

class PinMetadataCache(PinterestHashMap):
    
    def __init__(self, capacity: int = 10000, default_ttl: int = 3600):
        super().__init__(capacity)
        self.default_ttl = default_ttl
        self.timestamps = {}
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        result = super().put(key, value)
        if result:
            ttl = ttl or self.default_ttl
            self.timestamps[key] = time.time() + ttl
        return result
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.timestamps and time.time() > self.timestamps[key]:
            self.remove(key)
            del self.timestamps[key]
            return None
        
        return super().get(key)
    
    def remove(self, key: str) -> bool:
        result = super().remove(key)
        if result and key in self.timestamps:
            del self.timestamps[key]
        return result
    
    def cleanup_expired(self) -> int:
        current_time = time.time()
        expired_keys = [k for k, expiry in self.timestamps.items() if current_time > expiry]
        
        for key in expired_keys:
            self.remove(key)
        
        return len(expired_keys)

class UserSessionCache:
    
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.session_data = {}
    
    def get(self, session_id: str) -> Optional[Dict]:
        if session_id in self.cache:
            self.cache.move_to_end(session_id)
            return self.session_data[session_id]
        return None
    
    def put(self, session_id: str, data: Dict) -> None:
        if session_id in self.cache:
            self.cache.move_to_end(session_id)
        else:
            if len(self.cache) >= self.capacity:
                oldest = next(iter(self.cache))
                del self.cache[oldest]
                del self.session_data[oldest]
        
        self.cache[session_id] = True
        self.session_data[session_id] = data
    
    def remove(self, session_id: str) -> bool:
        if session_id in self.cache:
            del self.cache[session_id]
            del self.session_data[session_id]
            return True
        return False

class PinDeduplicator:
    
    def __init__(self):
        self.content_hashes = {}
        self.pin_hashes = {}
    
    def generate_content_hash(self, pin_data: Dict) -> str:
        normalized_data = {
            'image_url': pin_data.get('image_url', ''),
            'title': pin_data.get('title', '').lower().strip(),
            'description': pin_data.get('description', '').lower().strip(),
            'link': pin_data.get('link', '')
        }
        
        content_str = json.dumps(normalized_data, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def is_duplicate(self, pin_data: Dict) -> Tuple[bool, Optional[str]]:
        content_hash = self.generate_content_hash(pin_data)
        
        if content_hash in self.content_hashes:
            return True, self.content_hashes[content_hash]
        
        return False, None
    
    def add_pin(self, pin_id: str, pin_data: Dict) -> bool:
        is_duplicate, existing_pin_id = self.is_duplicate(pin_data)
        
        if is_duplicate:
            return False
        
        content_hash = self.generate_content_hash(pin_data)
        self.content_hashes[content_hash] = pin_id
        self.pin_hashes[pin_id] = content_hash
        return True
    
    def remove_pin(self, pin_id: str) -> bool:
        if pin_id in self.pin_hashes:
            content_hash = self.pin_hashes[pin_id]
            del self.content_hashes[content_hash]
            del self.pin_hashes[pin_id]
            return True
        return False

class ConsistentHashRing:
    
    def __init__(self, nodes: List[str] = None, replicas: int = 150):
        self.replicas = replicas
        self.ring = {}
        self.nodes = set()
        
        if nodes:
            for node in nodes:
                self.add_node(node)
    
    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def add_node(self, node: str) -> None:
        self.nodes.add(node)
        
        for i in range(self.replicas):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            self.ring[hash_value] = node
        
        self.sorted_keys = sorted(self.ring.keys())
    
    def remove_node(self, node: str) -> None:
        self.nodes.discard(node)
        
        for i in range(self.replicas):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            if hash_value in self.ring:
                del self.ring[hash_value]
        
        self.sorted_keys = sorted(self.ring.keys())
    
    def get_node(self, key: str) -> Optional[str]:
        if not self.ring:
            return None
        
        hash_value = self._hash(key)
        
        index = bisect.bisect_right(self.sorted_keys, hash_value)
        
        if index == len(self.sorted_keys):
            index = 0
        
        return self.ring[self.sorted_keys[index]]
    
    def get_distribution(self, keys: List[str]) -> Dict[str, int]:
        distribution = {node: 0 for node in self.nodes}
        
        for key in keys:
            node = self.get_node(key)
            if node:
                distribution[node] += 1
        
        return distribution

class PinterestCacheManager:
    
    def __init__(self):
        self.pin_cache = PinMetadataCache(capacity=50000)
        self.session_cache = UserSessionCache(capacity=10000)
        self.deduplicator = PinDeduplicator()
        self.hash_ring = ConsistentHashRing()
        
        cache_nodes = [f"cache_node_{i}" for i in range(4)]
        for node in cache_nodes:
            self.hash_ring.add_node(node)
    
    def cache_pin(self, pin_id: str, pin_data: Dict, ttl: int = 3600) -> bool:
        return self.pin_cache.put(pin_id, pin_data, ttl)
    
    def get_cached_pin(self, pin_id: str) -> Optional[Dict]:
        return self.pin_cache.get(pin_id)
    
    def cache_session(self, session_id: str, user_data: Dict) -> None:
        self.session_cache.put(session_id, user_data)
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        return self.session_cache.get(session_id)
    
    def deduplicate_pin(self, pin_id: str, pin_data: Dict) -> Tuple[bool, Optional[str]]:
        is_duplicate, duplicate_pin_id = self.deduplicator.is_duplicate(pin_data)
        
        if not is_duplicate:
            self.deduplicator.add_pin(pin_id, pin_data)
            return True, None
        
        return False, duplicate_pin_id
    
    def get_cache_node(self, key: str) -> Optional[str]:
        return self.hash_ring.get_node(key)
    
    def cleanup_expired(self) -> int:
        return self.pin_cache.cleanup_expired()
    
    def get_stats(self) -> Dict:
        return {
            'pin_cache': {
                'size': self.pin_cache.size,
                'capacity': self.pin_cache.capacity,
                'load_factor': self.pin_cache.size / self.pin_cache.capacity
            },
            'session_cache': {
                'active_sessions': len(self.session_cache.cache),
                'capacity': self.session_cache.capacity
            },
            'deduplication': {
                'tracked_pins': len(self.deduplicator.pin_hashes),
                'unique_content_hashes': len(self.deduplicator.content_hashes)
            },
            'hash_ring': {
                'nodes': list(self.hash_ring.nodes),
                'virtual_nodes': len(self.hash_ring.ring)
            }
        }
