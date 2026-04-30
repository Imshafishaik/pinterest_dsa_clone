"""
Recommendation Engine Feature for Pinterest Clone
Implements interest graph traversal with PageRank variant for recommendations
"""

import time
import random
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from core_dsa.graph import PinterestGraph
from core_dsa.hash_map import PinterestCacheManager
from core_dsa.priority_queue import KWayMerge

@dataclass
class Recommendation:
    """Recommendation with scoring metadata"""
    item_id: str
    item_type: str  # 'pin', 'board', 'user'
    score: float
    explanation: str
    factors: Dict[str, float]

class InterestGraphRecommender:
    """Recommendation engine using interest graph traversal and PageRank"""
    
    def __init__(self, graph: PinterestGraph, cache_manager: PinterestCacheManager):
        self.graph = graph
        self.cache_manager = cache_manager
        self.k_way_merger = KWayMerge()
        
        # Recommendation weights
        self.weights = {
            'graph_proximity': 0.35,
            'authority_score': 0.25,
            'collaborative_filtering': 0.20,
            'content_similarity': 0.15,
            'diversity_boost': 0.05
        }
        
        # PageRank scores cache
        self.authority_scores = {}
        self.last_authority_update = 0
        self.authority_update_interval = 3600  # 1 hour
    
    def recommend_pins(self, user_id: str, limit: int = 20, 
                      include_explanation: bool = True) -> List[Recommendation]:
        """
        Recommend pins using interest graph traversal and PageRank variant
        Implements "More like this" and board suggestions
        """
        # Update authority scores if needed
        self._update_authority_scores()
        
        # Get user's interest context
        user_context = self._get_user_interest_context(user_id)
        
        # Generate recommendations from different sources
        graph_recommendations = self._get_graph_based_recommendations(user_id, user_context, limit)
        authority_recommendations = self._get_authority_based_recommendations(user_id, user_context, limit)
        collaborative_recommendations = self._get_collaborative_recommendations(user_id, user_context, limit)
        
        # Merge recommendations using k-way merge
        all_recommendations = [
            graph_recommendations,
            authority_recommendations,
            collaborative_recommendations
        ]
        
        merged_recommendations = self._merge_recommendations(all_recommendations, limit)
        
        # Add explanations if requested
        if include_explanation:
            for rec in merged_recommendations:
                rec.explanation = self._generate_explanation(user_id, rec, user_context)
        
        return merged_recommendations
    
    def recommend_boards(self, user_id: str, limit: int = 10) -> List[Recommendation]:
        """Recommend boards based on user interests and social connections"""
        user_context = self._get_user_interest_context(user_id)
        
        # Get boards from user's social connections
        following_boards = self._get_following_users_boards(user_id)
        
        # Get boards similar to user's existing boards
        similar_boards = self._get_similar_boards(user_id)
        
        # Get trending boards
        trending_boards = self._get_trending_boards()
        
        # Score and merge board recommendations
        board_recommendations = []
        
        # Score following users' boards
        for board_id in following_boards:
            score = self._calculate_board_score(user_id, board_id, 'following', user_context)
            board_recommendations.append(Recommendation(
                item_id=board_id,
                item_type='board',
                score=score,
                explanation='',
                factors={'social_proximity': score}
            ))
        
        # Score similar boards
        for board_id in similar_boards:
            score = self._calculate_board_score(user_id, board_id, 'similar', user_context)
            board_recommendations.append(Recommendation(
                item_id=board_id,
                item_type='board',
                score=score,
                explanation='',
                factors={'content_similarity': score}
            ))
        
        # Sort and return top recommendations
        board_recommendations.sort(key=lambda x: x.score, reverse=True)
        return board_recommendations[:limit]
    
    def recommend_users(self, user_id: str, limit: int = 10) -> List[Recommendation]:
        """Recommend users to follow based on interest similarity"""
        user_context = self._get_user_interest_context(user_id)
        
        # Get users with similar interests
        similar_users = self._find_similar_users(user_id, user_context)
        
        user_recommendations = []
        for similar_user_id, similarity_score in similar_users:
            # Check if already following
            if similar_user_id not in self.graph.get_following(user_id):
                user_recommendations.append(Recommendation(
                    item_id=similar_user_id,
                    item_type='user',
                    score=similarity_score,
                    explanation='',
                    factors={'interest_similarity': similarity_score}
                ))
        
        # Sort and return top recommendations
        user_recommendations.sort(key=lambda x: x.score, reverse=True)
        return user_recommendations[:limit]
    
    def _get_user_interest_context(self, user_id: str) -> Dict:
        """Get comprehensive user interest context"""
        # Get user's saved pins
        user_pins = self.graph.get_user_pins(user_id)
        
        # Explore interests through graph traversal
        interests = self.graph.dfs_explore_interests(user_id, max_depth=3)
        
        # Get user's social connections
        following = self.graph.get_following(user_id)
        followers = self.graph.get_followers(user_id)
        
        # Calculate interest categories
        pin_categories = {}
        for pin_id in user_pins[:50]:  # Sample up to 50 pins
            pin_data = self.cache_manager.get_cached_pin(pin_id)
            if pin_data:
                category = pin_data.get('category', 'unknown')
                pin_categories[category] = pin_categories.get(category, 0) + 1
        
        return {
            'user_pins': user_pins,
            'interests': interests,
            'following': following,
            'followers': followers,
            'pin_categories': pin_categories,
            'social_influence': self.graph.get_influence_score(user_id)
        }
    
    def _get_graph_based_recommendations(self, user_id: str, context: Dict, limit: int) -> List[Recommendation]:
        """Get recommendations through interest graph traversal (BFS)"""
        recommendations = []
        user_pins = context['user_pins']
        
        # Find similar pins through BFS for each user pin
        similar_pins = set()
        for pin_id in user_pins[:20]:  # Sample up to 20 pins
            bfs_results = self.graph.bfs_find_similar_pins(pin_id, max_depth=2)
            similar_pins.update(bfs_results)
        
        # Remove pins user already has
        candidate_pins = similar_pins - set(user_pins)
        
        # Score candidates based on graph proximity
        for pin_id in candidate_pins:
            # Calculate graph proximity score
            proximity_score = self._calculate_graph_proximity(user_id, pin_id, context)
            
            recommendations.append(Recommendation(
                item_id=pin_id,
                item_type='pin',
                score=proximity_score,
                explanation='',
                factors={'graph_proximity': proximity_score}
            ))
        
        # Sort and return top recommendations
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit]
    
    def _get_authority_based_recommendations(self, user_id: str, context: Dict, limit: int) -> List[Recommendation]:
        """Get recommendations based on Pin authority (PageRank variant)"""
        recommendations = []
        
        # Get high-authority pins
        authority_pins = sorted(self.authority_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Filter and score authority pins
        for pin_id, authority_score in authority_pins[:limit * 3]:  # Get more candidates
            # Skip if user already has this pin
            if pin_id not in context['user_pins']:
                # Calculate authority-based score
                final_score = authority_score * self.weights['authority_score']
                
                # Boost for category preference
                pin_data = self.cache_manager.get_cached_pin(pin_id)
                if pin_data:
                    category = pin_data.get('category', 'unknown')
                    category_preference = context['pin_categories'].get(category, 0)
                    category_boost = min(category_preference / 10.0, 0.5)  # Max 50% boost
                    final_score *= (1.0 + category_boost)
                
                recommendations.append(Recommendation(
                    item_id=pin_id,
                    item_type='pin',
                    score=final_score,
                    explanation='',
                    factors={'authority_score': authority_score}
                ))
        
        # Sort and return top recommendations
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit]
    
    def _get_collaborative_recommendations(self, user_id: str, context: Dict, limit: int) -> List[Recommendation]:
        """Get recommendations through collaborative filtering"""
        recommendations = []
        following = context['following']
        
        # Get pins from users this user follows
        following_pins = {}
        for followed_user in following[:50]:  # Sample up to 50 followed users
            user_pins = self.graph.get_user_pins(followed_user)
            for pin_id in user_pins:
                if pin_id not in context['user_pins']:  # Skip pins user already has
                    if pin_id not in following_pins:
                        following_pins[pin_id] = []
                    following_pins[pin_id].append(followed_user)
        
        # Score based on how many followed users have each pin
        for pin_id, followed_by in following_pins.items():
            collaborative_score = len(followed_by) / len(following)
            
            # Weight by social influence of followed users
            influence_weight = sum(self.graph.get_influence_score(user) for user in followed_by) / len(followed_by)
            
            final_score = collaborative_score * influence_weight * self.weights['collaborative_filtering']
            
            recommendations.append(Recommendation(
                item_id=pin_id,
                item_type='pin',
                score=final_score,
                explanation='',
                factors={'collaborative_score': collaborative_score, 'influence_weight': influence_weight}
            ))
        
        # Sort and return top recommendations
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit]
    
    def _calculate_graph_proximity(self, user_id: str, pin_id: str, context: Dict) -> float:
        """Calculate graph proximity score between user and pin"""
        user_pins = context['user_pins']
        
        # Find shortest path through interest graph
        min_distance = float('inf')
        for user_pin in user_pins[:20]:  # Sample for performance
            # Check if pins are directly connected through BFS
            similar_pins = self.graph.bfs_find_similar_pins(user_pin, max_depth=2)
            if pin_id in similar_pins:
                # Found connection, calculate distance
                distance = similar_pins.index(pin_id) + 1  # 1-based distance
                min_distance = min(min_distance, distance)
        
        # Convert distance to proximity score (closer = higher score)
        if min_distance == float('inf'):
            proximity_score = 0.0
        else:
            proximity_score = 1.0 / min_distance
        
        return proximity_score * self.weights['graph_proximity']
    
    def _calculate_board_score(self, user_id: str, board_id: str, source: str, context: Dict) -> float:
        """Calculate board recommendation score"""
        base_score = 0.5
        
        if source == 'following':
            # Boards from followed users
            base_score = 0.7
        elif source == 'similar':
            # Boards similar to user's existing boards
            base_score = 0.6
        
        # Apply weights
        final_score = base_score * self.weights['graph_proximity']
        
        return final_score
    
    def _find_similar_users(self, user_id: str, context: Dict) -> List[Tuple[str, float]]:
        """Find users with similar interests"""
        user_pins = set(context['user_pins'])
        similar_users = []
        
        # Sample users from the graph (in production, use more sophisticated sampling)
        sample_size = min(1000, len(self.graph.interest_graph.nodes))
        sampled_nodes = random.sample(list(self.graph.interest_graph.nodes), sample_size)
        
        for node_id in sampled_nodes:
            # Skip if it's the same user or already following
            if node_id == user_id or node_id in context['following']:
                continue
            
            # Check if it's a user node
            node_data = self.graph.interest_graph.nodes.get(node_id, {})
            if node_data.get('type') != 'user':
                continue
            
            # Get their pins
            their_pins = set(self.graph.get_user_pins(node_id))
            
            # Calculate Jaccard similarity
            intersection = len(user_pins.intersection(their_pins))
            union = len(user_pins.union(their_pins))
            
            if union > 0:
                similarity = intersection / union
                if similarity > 0.1:  # Minimum similarity threshold
                    similar_users.append((node_id, similarity))
        
        # Sort by similarity
        similar_users.sort(key=lambda x: x[1], reverse=True)
        return similar_users
    
    def _get_following_users_boards(self, user_id: str) -> List[str]:
        """Get boards from users that this user follows"""
        following = self.graph.get_following(user_id)
        boards = set()
        
        for followed_user in following[:50]:  # Sample for performance
            user_interests = self.graph.dfs_explore_interests(followed_user, max_depth=2)
            boards.update(user_interests.get('boards', []))
        
        return list(boards)
    
    def _get_similar_boards(self, user_id: str) -> List[str]:
        """Get boards similar to user's existing boards"""
        user_interests = self.graph.dfs_explore_interests(user_id, max_depth=2)
        user_boards = set(user_interests.get('boards', []))
        
        similar_boards = set()
        for board_id in user_boards:
            # Find boards that share pins with this board
            board_pins = self.graph.get_board_pins(board_id)
            for pin_id in board_pins[:20]:  # Sample pins
                similar_pins = self.graph.bfs_find_similar_pins(pin_id, max_depth=1)
                for similar_pin in similar_pins:
                    # Find boards that contain this similar pin
                    # This is simplified - in production, maintain reverse index
                    pass
        
        return list(similar_boards)
    
    def _get_trending_boards(self) -> List[str]:
        """Get trending boards (simplified implementation)"""
        # In production, this would use real trending data
        # For now, return empty list
        return []
    
    def _merge_recommendations(self, recommendation_lists: List[List[Recommendation]], limit: int) -> List[Recommendation]:
        """Merge multiple recommendation lists using k-way merge"""
        # Convert to format expected by k-way merge
        scored_lists = []
        for rec_list in recommendation_lists:
            scored_list = [(rec, rec.score) for rec in rec_list]
            scored_list.sort(key=lambda x: x[1], reverse=True)
            scored_lists.append(scored_list)
        
        # Use k-way merge to get top recommendations
        merged = self.k_way_merger.merge_k_sorted_lists(scored_lists, limit)
        
        # Convert back to Recommendation objects and apply diversity boost
        final_recommendations = []
        seen_items = set()
        
        for item, score in merged:
            if item.item_id not in seen_items:
                # Apply small diversity boost
                diversity_boost = random.random() * 0.05
                item.score += diversity_boost
                item.factors['diversity_boost'] = diversity_boost
                
                final_recommendations.append(item)
                seen_items.add(item.item_id)
        
        return final_recommendations
    
    def _generate_explanation(self, user_id: str, recommendation: Recommendation, context: Dict) -> str:
        """Generate explanation for recommendation"""
        factors = recommendation.factors
        
        if 'graph_proximity' in factors and factors['graph_proximity'] > 0.5:
            return "Recommended because it's similar to pins you've saved"
        elif 'authority_score' in factors and factors['authority_score'] > 0.7:
            return "Popular pin that matches your interests"
        elif 'collaborative_score' in factors and factors['collaborative_score'] > 0.5:
            return "Pinned by users you follow"
        elif 'content_similarity' in factors:
            return "Similar to content you've engaged with"
        else:
            return "Recommended based on your interests"
    
    def _update_authority_scores(self) -> None:
        """Update PageRank authority scores if needed"""
        current_time = time.time()
        
        if current_time - self.last_authority_update > self.authority_update_interval:
            self.authority_scores = self.graph.calculate_pin_authority()
            self.last_authority_update = current_time
    
    def get_recommendation_stats(self) -> Dict:
        """Get recommendation engine statistics"""
        return {
            'authority_scores_count': len(self.authority_scores),
            'last_authority_update': self.last_authority_update,
            'weights': self.weights,
            'cache_stats': self.cache_manager.get_stats()
        }

class RecommendationAnalytics:
    """Analytics for recommendation performance"""
    
    def __init__(self):
        self.recommendation_logs = []
        self.user_interactions = {}
        self.performance_metrics = {
            'avg_generation_time': 0.0,
            'click_through_rate': 0.0,
            'conversion_rate': 0.0
        }
    
    def log_recommendation(self, user_id: str, recommendations: List[Recommendation], 
                          generation_time: float) -> None:
        """Log recommendation generation"""
        self.recommendation_logs.append({
            'user_id': user_id,
            'recommendations': [(rec.item_id, rec.item_type, rec.score) for rec in recommendations],
            'generation_time': generation_time,
            'timestamp': time.time()
        })
        
        # Update performance metrics
        if self.recommendation_logs:
            avg_time = sum(log['generation_time'] for log in self.recommendation_logs[-100:]) / len(self.recommendation_logs[-100:])
            self.performance_metrics['avg_generation_time'] = avg_time
    
    def log_interaction(self, user_id: str, item_id: str, interaction_type: str) -> None:
        """Log user interaction with recommended items"""
        if user_id not in self.user_interactions:
            self.user_interactions[user_id] = []
        
        self.user_interactions[user_id].append({
            'item_id': item_id,
            'interaction_type': interaction_type,
            'timestamp': time.time()
        })
    
    def calculate_ctr(self, user_id: str) -> float:
        """Calculate click-through rate for user"""
        if user_id not in self.user_interactions:
            return 0.0
        
        interactions = self.user_interactions[user_id]
        clicks = sum(1 for i in interactions if i['interaction_type'] in ['click', 'save'])
        
        # Find recommendation sessions for this user
        user_recommendations = [log for log in self.recommendation_logs if log['user_id'] == user_id]
        total_recommendations = sum(len(log['recommendations']) for log in user_recommendations)
        
        if total_recommendations == 0:
            return 0.0
        
        return clicks / total_recommendations
    
    def get_analytics_report(self) -> Dict:
        """Get comprehensive analytics report"""
        # Calculate overall CTR
        total_clicks = sum(
            len([i for i in interactions if i['interaction_type'] in ['click', 'save']])
            for interactions in self.user_interactions.values()
        )
        
        total_recommendations = sum(len(log['recommendations']) for log in self.recommendation_logs)
        overall_ctr = total_clicks / total_recommendations if total_recommendations > 0 else 0.0
        
        return {
            'performance_metrics': self.performance_metrics,
            'overall_ctr': overall_ctr,
            'total_recommendations_made': len(self.recommendation_logs),
            'active_users': len(self.user_interactions),
            'avg_recommendations_per_user': total_recommendations / len(self.user_interactions) if self.user_interactions else 0
        }
