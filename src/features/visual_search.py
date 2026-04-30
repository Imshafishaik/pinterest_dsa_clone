"""
Visual Search Feature for Pinterest Clone
Implements K-d Tree for approximate nearest-neighbor search with CNN embeddings
"""

import numpy as np
from core_dsa.tree import AVLTree, TimestampIndex
from typing import Optional, Any, Dict, List, Tuple
from dataclasses import dataclass
import time
import pickle
import os

@dataclass
class ImageEmbedding:
    """Image embedding with metadata"""
    pin_id: str
    embedding: np.ndarray
    image_url: str
    metadata: Dict = None

class KDTreeNode:
    """K-d Tree node for efficient nearest neighbor search"""
    
    def __init__(self, point: np.ndarray, pin_id: str, axis: int = 0):
        self.point = point
        self.pin_id = pin_id
        self.axis = axis
        self.left = None
        self.right = None
        self.metadata = {}

class KDTree:
    """K-d Tree implementation for approximate nearest neighbor search"""
    
    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        self.root = None
        self.size = 0
    
    def build_tree(self, points: List[Tuple[np.ndarray, str]]) -> None:
        """Build K-d tree from list of points"""
        if not points:
            self.root = None
            return
        
        self.root = self._build_tree_recursive(points, 0)
        self.size = len(points)
    
    def _build_tree_recursive(self, points: List[Tuple[np.ndarray, str]], depth: int) -> KDTreeNode:
        """Recursively build K-d tree"""
        if not points:
            return None
        
        # Select axis based on depth
        axis = depth % self.dimension
        
        # Sort points by selected axis and select median
        points.sort(key=lambda x: x[0][axis])
        median_idx = len(points) // 2
        
        # Create node
        node = KDTreeNode(points[median_idx][0], points[median_idx][1], axis)
        
        # Recursively build subtrees
        node.left = self._build_tree_recursive(points[:median_idx], depth + 1)
        node.right = self._build_tree_recursive(points[median_idx + 1:], depth + 1)
        
        return node
    
    def nearest_neighbor(self, query_point: np.ndarray, k: int = 1) -> List[Tuple[str, float]]:
        """Find k nearest neighbors to query point"""
        if self.root is None:
            return []
        
        neighbors = []
        self._nearest_neighbor_recursive(self.root, query_point, k, neighbors)
        
        # Sort by distance and return top k
        neighbors.sort(key=lambda x: x[1])
        return neighbors[:k]
    
    def _nearest_neighbor_recursive(self, node: KDTreeNode, query_point: np.ndarray, 
                                  k: int, neighbors: List[Tuple[str, float]]) -> None:
        """Recursive nearest neighbor search"""
        if node is None:
            return
        
        # Calculate distance to current node
        distance = np.linalg.norm(query_point - node.point)
        
        # Add to neighbors if we have space or if closer than farthest neighbor
        if len(neighbors) < k:
            neighbors.append((node.pin_id, distance))
        elif distance < neighbors[-1][1]:
            neighbors[-1] = (node.pin_id, distance)
            neighbors.sort(key=lambda x: x[1])
        
        # Choose which side to explore first
        axis = node.axis
        if query_point[axis] < node.point[axis]:
            self._nearest_neighbor_recursive(node.left, query_point, k, neighbors)
            
            # Check if we need to explore the other side
            if len(neighbors) < k or abs(query_point[axis] - node.point[axis]) < neighbors[-1][1]:
                self._nearest_neighbor_recursive(node.right, query_point, k, neighbors)
        else:
            self._nearest_neighbor_recursive(node.right, query_point, k, neighbors)
            
            # Check if we need to explore the other side
            if len(neighbors) < k or abs(query_point[axis] - node.point[axis]) < neighbors[-1][1]:
                self._nearest_neighbor_recursive(node.left, query_point, k, neighbors)
    
    def range_search(self, query_point: np.ndarray, radius: float) -> List[Tuple[str, float]]:
        """Find all points within radius of query point"""
        if self.root is None:
            return []
        
        results = []
        self._range_search_recursive(self.root, query_point, radius, results)
        
        # Sort by distance
        results.sort(key=lambda x: x[1])
        return results
    
    def _range_search_recursive(self, node: KDTreeNode, query_point: np.ndarray, 
                              radius: float, results: List[Tuple[str, float]]) -> None:
        """Recursive range search"""
        if node is None:
            return
        
        # Calculate distance to current node
        distance = np.linalg.norm(query_point - node.point)
        
        # Add if within radius
        if distance <= radius:
            results.append((node.pin_id, distance))
        
        # Check which branches to explore
        axis = node.axis
        axis_distance = abs(query_point[axis] - node.point[axis])
        
        # Always explore the side that contains the query point
        if query_point[axis] < node.point[axis]:
            self._range_search_recursive(node.left, query_point, radius, results)
            
            # Explore other side if within radius
            if axis_distance <= radius:
                self._range_search_recursive(node.right, query_point, radius, results)
        else:
            self._range_search_recursive(node.right, query_point, radius, results)
            
            # Explore other side if within radius
            if axis_distance <= radius:
                self._range_search_recursive(node.left, query_point, radius, results)

class MockCNNEmbedder:
    """Mock CNN embedder for demonstration (in production, use real CNN)"""
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        np.random.seed(42)  # For reproducible results
    
    def extract_embedding(self, image_path: str) -> np.ndarray:
        """Extract CNN embedding from image (mock implementation)"""
        # In production, this would use a real CNN model
        # For now, generate pseudo-random but consistent embeddings
        hash_val = hash(image_path) % (2**32)
        np.random.seed(hash_val)
        embedding = np.random.randn(self.embedding_dim)
        
        # Normalize to unit vector
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding

class VisualSearchEngine:
    """Visual search engine using CNN embeddings and K-d Tree"""
    
    def __init__(self, embedding_dim: int = 128, tree_path: str = None):
        self.embedding_dim = embedding_dim
        self.embedder = MockCNNEmbedder(embedding_dim)
        self.kd_tree = KDTree(embedding_dim)
        self.embeddings = {}  # pin_id -> ImageEmbedding
        
        # Load existing tree if path provided
        if tree_path and os.path.exists(tree_path):
            self.load_tree(tree_path)
    
    def index_image(self, pin_id: str, image_url: str, metadata: Dict = None) -> None:
        """Index an image for visual search"""
        # Extract embedding
        embedding = self.embedder.extract_embedding(image_url)
        
        # Store embedding
        image_embedding = ImageEmbedding(
            pin_id=pin_id,
            embedding=embedding,
            image_url=image_url,
            metadata=metadata or {}
        )
        
        self.embeddings[pin_id] = image_embedding
        
        # Rebuild tree (in production, use incremental updates)
        self._rebuild_tree()
    
    def _rebuild_tree(self) -> None:
        """Rebuild K-d tree with current embeddings"""
        points = [(emb.embedding, emb.pin_id) for emb in self.embeddings.values()]
        self.kd_tree.build_tree(points)
    
    def search_similar_images(self, query_image_url: str, k: int = 10, 
                            max_distance: float = 0.5) -> List[Dict]:
        """Find visually similar images using K-d Tree"""
        start_time = time.time()
        
        # Extract query embedding
        query_embedding = self.embedder.extract_embedding(query_image_url)
        
        # Search for nearest neighbors
        neighbors = self.kd_tree.nearest_neighbor(query_embedding, k)
        
        # Filter by distance and format results
        results = []
        for pin_id, distance in neighbors:
            if distance <= max_distance:
                image_embedding = self.embeddings[pin_id]
                
                result = {
                    'pin_id': pin_id,
                    'image_url': image_embedding.image_url,
                    'similarity_score': 1.0 - distance,  # Convert distance to similarity
                    'distance': distance,
                    'metadata': image_embedding.metadata
                }
                results.append(result)
        
        search_time = time.time() - start_time
        
        return {
            'query_image': query_image_url,
            'results': results,
            'search_time_ms': search_time * 1000,
            'total_results': len(results)
        }
    
    def range_search(self, query_image_url: str, radius: float = 0.3) -> List[Dict]:
        """Find all images within similarity radius"""
        start_time = time.time()
        
        # Extract query embedding
        query_embedding = self.embedder.extract_embedding(query_image_url)
        
        # Perform range search
        neighbors = self.kd_tree.range_search(query_embedding, radius)
        
        # Format results
        results = []
        for pin_id, distance in neighbors:
            image_embedding = self.embeddings[pin_id]
            
            result = {
                'pin_id': pin_id,
                'image_url': image_embedding.image_url,
                'similarity_score': 1.0 - distance,
                'distance': distance,
                'metadata': image_embedding.metadata
            }
            results.append(result)
        
        search_time = time.time() - start_time
        
        return {
            'query_image': query_image_url,
            'results': results,
            'search_time_ms': search_time * 1000,
            'radius': radius,
            'total_results': len(results)
        }
    
    def calculate_similarity(self, image_url_1: str, image_url_2: str) -> float:
        """Calculate similarity between two images"""
        embedding_1 = self.embedder.extract_embedding(image_url_1)
        embedding_2 = self.embedder.extract_embedding(image_url_2)
        
        # Calculate cosine similarity
        similarity = np.dot(embedding_1, embedding_2)
        return similarity
    
    def get_embedding_stats(self) -> Dict:
        """Get embedding and tree statistics"""
        if not self.embeddings:
            return {'total_embeddings': 0, 'tree_size': 0}
        
        # Calculate embedding statistics
        all_embeddings = np.array([emb.embedding for emb in self.embeddings.values()])
        
        stats = {
            'total_embeddings': len(self.embeddings),
            'embedding_dimension': self.embedding_dim,
            'tree_size': self.kd_tree.size,
            'avg_embedding_norm': np.mean(np.linalg.norm(all_embeddings, axis=1)),
            'embedding_std': np.std(all_embeddings)
        }
        
        return stats
    
    def save_tree(self, file_path: str) -> bool:
        """Save K-d tree and embeddings to file"""
        try:
            tree_data = {
                'embeddings': self.embeddings,
                'kd_tree': self.kd_tree
            }
            
            with open(file_path, 'wb') as f:
                pickle.dump(tree_data, f)
            
            return True
        except Exception as e:
            print(f"Error saving tree: {e}")
            return False
    
    def load_tree(self, file_path: str) -> bool:
        """Load K-d tree and embeddings from file"""
        try:
            with open(file_path, 'rb') as f:
                tree_data = pickle.load(f)
            
            self.embeddings = tree_data['embeddings']
            self.kd_tree = tree_data['kd_tree']
            
            return True
        except Exception as e:
            print(f"Error loading tree: {e}")
            return False
    
    def remove_image(self, pin_id: str) -> bool:
        """Remove image from index"""
        if pin_id in self.embeddings:
            del self.embeddings[pin_id]
            self._rebuild_tree()
            return True
        return False
    
    def batch_index_images(self, images: List[Tuple[str, str, Dict]]) -> Dict:
        """Index multiple images in batch"""
        start_time = time.time()
        indexed_count = 0
        
        for pin_id, image_url, metadata in images:
            try:
                self.index_image(pin_id, image_url, metadata)
                indexed_count += 1
            except Exception as e:
                print(f"Error indexing image {pin_id}: {e}")
        
        indexing_time = time.time() - start_time
        
        return {
            'total_images': len(images),
            'indexed_count': indexed_count,
            'failed_count': len(images) - indexed_count,
            'indexing_time_ms': indexing_time * 1000
        }

class VisualSearchAnalytics:
    """Analytics for visual search performance"""
    
    def __init__(self):
        self.search_logs = []
        self.performance_metrics = {
            'avg_search_time_ms': 0.0,
            'avg_results_count': 0.0,
            'avg_similarity_score': 0.0
        }
    
    def log_search(self, search_data: Dict) -> None:
        """Log visual search query"""
        self.search_logs.append({
            'query_image': search_data.get('query_image', ''),
            'results_count': search_data.get('total_results', 0),
            'search_time_ms': search_data.get('search_time_ms', 0),
            'timestamp': time.time()
        })
        
        # Update performance metrics
        if self.search_logs:
            recent_logs = self.search_logs[-100:]  # Last 100 searches
            
            avg_time = sum(log['search_time_ms'] for log in recent_logs) / len(recent_logs)
            avg_results = sum(log['results_count'] for log in recent_logs) / len(recent_logs)
            
            self.performance_metrics['avg_search_time_ms'] = avg_time
            self.performance_metrics['avg_results_count'] = avg_results
    
    def log_interaction(self, query_image: str, clicked_pin_id: str, similarity_score: float) -> None:
        """Log user interaction with search results"""
        # This would be used to improve search quality
        pass
    
    def get_analytics_report(self) -> Dict:
        """Get comprehensive analytics report"""
        return {
            'performance_metrics': self.performance_metrics,
            'total_searches': len(self.search_logs),
            'search_frequency': len(self.search_logs) / (time.time() - self.search_logs[0]['timestamp']) / 3600 if self.search_logs else 0,  # searches per hour
            'recent_searches': self.search_logs[-10:]  # Last 10 searches
        }

class PinterestLens:
    """Pinterest Lens - Advanced visual search with multiple features"""
    
    def __init__(self, visual_search_engine: VisualSearchEngine):
        self.visual_search = visual_search_engine
        self.analytics = VisualSearchAnalytics()
        
        # Search modes
        self.search_modes = {
            'similar': self._similar_search,
            'exact': self._exact_search,
            'color': self._color_search,
            'style': self._style_search
        }
    
    def search(self, query_image_url: str, mode: str = 'similar', 
              k: int = 10, **kwargs) -> Dict:
        """Perform visual search with specified mode"""
        if mode not in self.search_modes:
            mode = 'similar'
        
        # Perform search
        search_results = self.search_modes[mode](query_image_url, k, **kwargs)
        
        # Log search
        self.analytics.log_search(search_results)
        
        return search_results
    
    def _similar_search(self, query_image_url: str, k: int, **kwargs) -> Dict:
        """Standard similarity search"""
        return self.visual_search.search_similar_images(query_image_url, k)
    
    def _exact_search(self, query_image_url: str, k: int, **kwargs) -> Dict:
        """Exact match search (lower distance threshold)"""
        return self.visual_search.search_similar_images(
            query_image_url, k, max_distance=0.1
        )
    
    def _color_search(self, query_image_url: str, k: int, **kwargs) -> Dict:
        """Color-based search (simplified - would need color extraction)"""
        # For now, use standard search but could be enhanced with color histograms
        return self.visual_search.search_similar_images(query_image_url, k)
    
    def _style_search(self, query_image_url: str, k: int, **kwargs) -> Dict:
        """Style-based search (simplified - would need style classification)"""
        # For now, use standard search but could be enhanced with style features
        return self.visual_search.search_similar_images(query_image_url, k)
    
    def get_search_analytics(self) -> Dict:
        """Get visual search analytics"""
        return self.analytics.get_analytics_report()
    
    def get_engine_stats(self) -> Dict:
        """Get visual search engine statistics"""
        return self.visual_search.get_embedding_stats()
