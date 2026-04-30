"""
Graph Data Structure for Pinterest Clone
Implements social graph and interest graph with BFS/DFS and PageRank algorithms
"""

import networkx as nx
from typing import Dict, List, Set, Tuple, Optional
from collections import deque
import random

class PinterestGraph:
    """
    Pinterest-specific graph implementation for:
    - Social graph (user-following relationships)
    - Interest graph (user-pin-board relationships)
    """
    
    def __init__(self):
        self.social_graph = nx.DiGraph()  # User following relationships
        self.interest_graph = nx.Graph()   # User-Pin-Board interest relationships
        self.board_graph = nx.DiGraph()    # Board hierarchy and ownership
        
    # Social Graph Methods
    def add_user(self, user_id: str, user_data: Dict = None):
        """Add a user to the social graph"""
        self.social_graph.add_node(user_id, **(user_data or {}))
    
    def follow_user(self, follower_id: str, following_id: str):
        """Create a following relationship"""
        self.social_graph.add_edge(follower_id, following_id)
    
    def get_followers(self, user_id: str) -> List[str]:
        """Get all followers of a user"""
        return list(self.social_graph.predecessors(user_id))
    
    def get_following(self, user_id: str) -> List[str]:
        """Get all users that this user follows"""
        return list(self.social_graph.successors(user_id))
    
    def get_mutual_followers(self, user_id: str) -> List[str]:
        """Get users who follow each other (mutual following)"""
        followers = set(self.get_followers(user_id))
        following = set(self.get_following(user_id))
        return list(followers.intersection(following))
    
    # Interest Graph Methods
    def add_pin(self, pin_id: str, pin_data: Dict = None):
        """Add a pin to the interest graph"""
        self.interest_graph.add_node(pin_id, type='pin', **(pin_data or {}))
    
    def add_board(self, board_id: str, board_data: Dict = None):
        """Add a board to the interest graph"""
        self.interest_graph.add_node(board_id, type='board', **(board_data or {}))
    
    def save_pin_to_board(self, user_id: str, pin_id: str, board_id: str):
        """Connect user-pin-board relationship"""
        self.interest_graph.add_edge(user_id, pin_id, relationship='saved')
        self.interest_graph.add_edge(pin_id, board_id, relationship='belongs_to')
        self.interest_graph.add_edge(user_id, board_id, relationship='owns')
    
    def get_user_pins(self, user_id: str) -> List[str]:
        """Get all pins saved by a user"""
        return [n for n in self.interest_graph.neighbors(user_id) 
                if self.interest_graph.nodes[n].get('type') == 'pin']
    
    def get_board_pins(self, board_id: str) -> List[str]:
        """Get all pins in a board"""
        return [n for n in self.interest_graph.neighbors(board_id)
                if self.interest_graph.nodes[n].get('type') == 'pin']
    
    # Graph Traversal Algorithms
    def bfs_find_similar_pins(self, pin_id: str, max_depth: int = 3) -> List[str]:
        """
        Find similar pins using BFS traversal through interest graph
        Returns pins within max_depth steps
        """
        visited = set()
        queue = deque([(pin_id, 0)])
        similar_pins = []
        
        while queue:
            current_pin, depth = queue.popleft()
            
            if depth >= max_depth:
                continue
                
            if current_pin != pin_id and self.interest_graph.nodes[current_pin].get('type') == 'pin':
                similar_pins.append(current_pin)
            
            for neighbor in self.interest_graph.neighbors(current_pin):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))
        
        return similar_pins
    
    def dfs_explore_interests(self, user_id: str, max_depth: int = 2) -> Dict:
        """
        Explore user interests using DFS
        Returns categorized interests (pins, boards, related users)
        """
        visited = set()
        interests = {'pins': [], 'boards': [], 'users': []}
        
        def dfs(node, depth):
            if depth >= max_depth or node in visited:
                return
            
            visited.add(node)
            node_type = self.interest_graph.nodes[node].get('type')
            
            if node_type == 'pin':
                interests['pins'].append(node)
            elif node_type == 'board':
                interests['boards'].append(node)
            elif node_type == 'user':
                interests['users'].append(node)
            
            for neighbor in self.interest_graph.neighbors(node):
                dfs(neighbor, depth + 1)
        
        dfs(user_id, 0)
        return interests
    
    # PageRank Algorithm for Pin Authority
    def calculate_pin_authority(self, damping: float = 0.85, max_iter: int = 100) -> Dict[str, float]:
        """
        Calculate pin authority using PageRank variant
        Higher authority = more important/relevant pins
        """
        # Create subgraph with only pins and their relationships
        pin_nodes = [n for n, data in self.interest_graph.nodes(data=True) 
                    if data.get('type') == 'pin']
        pin_subgraph = self.interest_graph.subgraph(pin_nodes)
        
        # Calculate PageRank
        pagerank_scores = nx.pagerank(pin_subgraph, alpha=damping, max_iter=max_iter)
        
        return pagerank_scores
    
    # Recommendation Algorithm
    def recommend_pins(self, user_id: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Recommend pins based on:
        1. User's interest graph traversal
        2. Pin authority scores
        3. Similar users' preferences
        """
        # Get user's saved pins
        user_pins = self.get_user_pins(user_id)
        
        # Find similar pins through BFS
        similar_pins = set()
        for pin in user_pins:
            similar_pins.update(self.bfs_find_similar_pins(pin, max_depth=2))
        
        # Remove pins user already has
        candidate_pins = similar_pins - set(user_pins)
        
        # Calculate authority scores
        authority_scores = self.calculate_pin_authority()
        
        # Score candidates based on authority and similarity
        recommendations = []
        for pin in candidate_pins:
            score = authority_scores.get(pin, 0)
            recommendations.append((pin, score))
        
        # Sort by score and return top-k
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:top_k]
    
    # Social Features
    def get_influence_score(self, user_id: str) -> float:
        """Calculate user influence based on social graph metrics"""
        followers_count = len(self.get_followers(user_id))
        following_count = len(self.get_following(user_id))
        
        # Influence = followers / (followers + following) with damping
        if followers_count + following_count == 0:
            return 0.0
        
        return followers_count / (followers_count + following_count)
    
    def get_social_distance(self, user1_id: str, user2_id: str) -> int:
        """Calculate social distance between two users"""
        try:
            return nx.shortest_path_length(self.social_graph, user1_id, user2_id)
        except nx.NetworkXNoPath:
            return float('inf')
    
    # Visualization Support
    def get_graph_stats(self) -> Dict:
        """Get comprehensive graph statistics"""
        return {
            'social_graph': {
                'nodes': self.social_graph.number_of_nodes(),
                'edges': self.social_graph.number_of_edges(),
                'density': nx.density(self.social_graph),
                'avg_clustering': nx.average_clustering(self.social_graph.to_undirected())
            },
            'interest_graph': {
                'nodes': self.interest_graph.number_of_nodes(),
                'edges': self.interest_graph.number_of_edges(),
                'density': nx.density(self.interest_graph),
                'components': nx.number_connected_components(self.interest_graph)
            }
        }
