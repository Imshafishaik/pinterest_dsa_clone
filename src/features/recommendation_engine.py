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
    item_id: str
    item_type: str
    score: float
    explanation: str
    factors: Dict[str, float]

class InterestGraphRecommender:
    
    def __init__(self, graph: PinterestGraph, cache_manager: PinterestCacheManager):
        self.graph = graph
        self.cache_manager = cache_manager
        self.k_way_merger = KWayMerge()
        
        self.weights = {
            'graph_proximity': 0.35,
            'authority_score': 0.25,
            'collaborative_filtering': 0.20,
            'content_similarity': 0.15,
            'diversity_boost': 0.05
        }
        
        self.authority_scores = {}
        self.last_authority_update = 0
        self.authority_update_interval = 3600
    
    def recommend_pins(self, user_id: str, limit: int = 20, 
                      include_explanation: bool = True) -> List[Recommendation]:
        self._update_authority_scores()
        
        user_context = self._get_user_interest_context(user_id)
        
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
        
        if include_explanation:
            for rec in merged_recommendations:
                rec.explanation = self._generate_explanation(user_id, rec, user_context)
        
        return merged_recommendations
    
    def recommend_boards(self, user_id: str, limit: int = 10) -> List[Recommendation]:
        user_context = self._get_user_interest_context(user_id)
        
        following_boards = self._get_following_users_boards(user_id)
        
        similar_boards = self._get_similar_boards(user_id)
        
        trending_boards = self._get_trending_boards()
        
        board_recommendations = []
        
        for board_id in following_boards:
            score = self._calculate_board_score(user_id, board_id, 'following', user_context)
            board_recommendations.append(Recommendation(
                item_id=board_id,
                item_type='board',
                score=score,
                explanation='',
                factors={'social_proximity': score}
            ))
        
        for board_id in similar_boards:
            score = self._calculate_board_score(user_id, board_id, 'similar', user_context)
            board_recommendations.append(Recommendation(
                item_id=board_id,
                item_type='board',
                score=score,
                explanation='',
                factors={'content_similarity': score}
            ))
        
        board_recommendations.sort(key=lambda x: x.score, reverse=True)
        return board_recommendations[:limit]
    
    def recommend_users(self, user_id: str, limit: int = 10) -> List[Recommendation]:
        user_context = self._get_user_interest_context(user_id)
        
        similar_users = self._find_similar_users(user_id, user_context)
        
        user_recommendations = []
        for similar_user_id, similarity_score in similar_users:
            if similar_user_id not in self.graph.get_following(user_id):
                user_recommendations.append(Recommendation(
                    item_id=similar_user_id,
                    item_type='user',
                    score=similarity_score,
                    explanation='',
                    factors={'interest_similarity': similarity_score}
                ))
        
        user_recommendations.sort(key=lambda x: x.score, reverse=True)
        return user_recommendations[:limit]
    
    def _get_user_interest_context(self, user_id: str) -> Dict:
        user_pins = self.graph.get_user_pins(user_id)
        
        interests = self.graph.dfs_explore_interests(user_id, max_depth=3)
        
        following = self.graph.get_following(user_id)
        followers = self.graph.get_followers(user_id)
        
        pin_categories = {}
        for pin_id in user_pins[:50]:
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
        recommendations = []
        user_pins = context['user_pins']
        
        similar_pins = set()
        for pin_id in user_pins[:20]:
            bfs_results = self.graph.bfs_find_similar_pins(pin_id, max_depth=2)
            similar_pins.update(bfs_results)
        
        candidate_pins = similar_pins - set(user_pins)
        
        for pin_id in candidate_pins:
            proximity_score = self._calculate_graph_proximity(user_id, pin_id, context)
            
            recommendations.append(Recommendation(
                item_id=pin_id,
                item_type='pin',
                score=proximity_score,
                explanation='',
                factors={'graph_proximity': proximity_score}
            ))
        
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit]
    
    def _get_authority_based_recommendations(self, user_id: str, context: Dict, limit: int) -> List[Recommendation]:
        recommendations = []
        
        authority_pins = sorted(self.authority_scores.items(), key=lambda x: x[1], reverse=True)
        
        for pin_id, authority_score in authority_pins[:limit * 3]:
            if pin_id not in context['user_pins']:
                final_score = authority_score * self.weights['authority_score']
                
                pin_data = self.cache_manager.get_cached_pin(pin_id)
                if pin_data:
                    category = pin_data.get('category', 'unknown')
                    category_preference = context['pin_categories'].get(category, 0)
                    category_boost = min(category_preference / 10.0, 0.5)
                    final_score *= (1.0 + category_boost)
                
                recommendations.append(Recommendation(
                    item_id=pin_id,
                    item_type='pin',
                    score=final_score,
                    explanation='',
                    factors={'authority_score': authority_score}
                ))
        
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit]
    
    def _get_collaborative_recommendations(self, user_id: str, context: Dict, limit: int) -> List[Recommendation]:
        recommendations = []
        following = context['following']
        
        following_pins = {}
        for followed_user in following[:50]:
            user_pins = self.graph.get_user_pins(followed_user)
            for pin_id in user_pins:
                if pin_id not in context['user_pins']:
                    if pin_id not in following_pins:
                        following_pins[pin_id] = []
                    following_pins[pin_id].append(followed_user)
        
        for pin_id, followed_by in following_pins.items():
            collaborative_score = len(followed_by) / len(following)
            
            influence_weight = sum(self.graph.get_influence_score(user) for user in followed_by) / len(followed_by)
            
            final_score = collaborative_score * influence_weight * self.weights['collaborative_filtering']
            
            recommendations.append(Recommendation(
                item_id=pin_id,
                item_type='pin',
                score=final_score,
                explanation='',
                factors={'collaborative_score': collaborative_score, 'influence_weight': influence_weight}
            ))
        
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit]
    
    def _calculate_graph_proximity(self, user_id: str, pin_id: str, context: Dict) -> float:
        user_pins = context['user_pins']
        
        min_distance = float('inf')
        for user_pin in user_pins[:20]:
            similar_pins = self.graph.bfs_find_similar_pins(user_pin, max_depth=2)
            if pin_id in similar_pins:
                distance = similar_pins.index(pin_id) + 1
                min_distance = min(min_distance, distance)
        
        if min_distance == float('inf'):
            proximity_score = 0.0
        else:
            proximity_score = 1.0 / min_distance
        
        return proximity_score * self.weights['graph_proximity']
    
    def _calculate_board_score(self, user_id: str, board_id: str, source: str, context: Dict) -> float:
        base_score = 0.5
        
        if source == 'following':
            base_score = 0.7
        elif source == 'similar':
            base_score = 0.6
        
        final_score = base_score * self.weights['graph_proximity']
        
        return final_score
    
    def _find_similar_users(self, user_id: str, context: Dict) -> List[Tuple[str, float]]:
        user_pins = set(context['user_pins'])
        similar_users = []
        
        sample_size = min(1000, len(self.graph.interest_graph.nodes))
        sampled_nodes = random.sample(list(self.graph.interest_graph.nodes), sample_size)
        
        for node_id in sampled_nodes:
            if node_id == user_id or node_id in context['following']:
                continue
            
            node_data = self.graph.interest_graph.nodes.get(node_id, {})
            if node_data.get('type') != 'user':
                continue
            
            their_pins = set(self.graph.get_user_pins(node_id))
            
            intersection = len(user_pins.intersection(their_pins))
            union = len(user_pins.union(their_pins))
            
            if union > 0:
                similarity = intersection / union
                if similarity > 0.1:
                    similar_users.append((node_id, similarity))
        
        similar_users.sort(key=lambda x: x[1], reverse=True)
        return similar_users
    
    def _get_following_users_boards(self, user_id: str) -> List[str]:
        following = self.graph.get_following(user_id)
        boards = set()
        
        for followed_user in following[:50]:
            user_interests = self.graph.dfs_explore_interests(followed_user, max_depth=2)
            boards.update(user_interests.get('boards', []))
        
        return list(boards)
    
    def _get_similar_boards(self, user_id: str) -> List[str]:
        user_interests = self.graph.dfs_explore_interests(user_id, max_depth=2)
        user_boards = set(user_interests.get('boards', []))
        
        similar_boards = set()
        for board_id in user_boards:
            board_pins = self.graph.get_board_pins(board_id)
            for pin_id in board_pins[:20]:
                similar_pins = self.graph.bfs_find_similar_pins(pin_id, max_depth=1)
                for similar_pin in similar_pins:
                    pass
        
        return list(similar_boards)
    
    def _get_trending_boards(self) -> List[str]:
        return []
    
    def _merge_recommendations(self, recommendation_lists: List[List[Recommendation]], limit: int) -> List[Recommendation]:
        scored_lists = []
        for rec_list in recommendation_lists:
            scored_list = [(rec, rec.score) for rec in rec_list]
            scored_list.sort(key=lambda x: x[1], reverse=True)
            scored_lists.append(scored_list)
        
        merged = self.k_way_merger.merge_k_sorted_lists(scored_lists, limit)
        
        final_recommendations = []
        seen_items = set()
        
        for item, score in merged:
            if item.item_id not in seen_items:
                diversity_boost = random.random() * 0.05
                item.score += diversity_boost
                item.factors['diversity_boost'] = diversity_boost
                
                final_recommendations.append(item)
                seen_items.add(item.item_id)
        
        return final_recommendations
    
    def _generate_explanation(self, user_id: str, recommendation: Recommendation, context: Dict) -> str:
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
        current_time = time.time()
        
        if current_time - self.last_authority_update > self.authority_update_interval:
            self.authority_scores = self.graph.calculate_pin_authority()
            self.last_authority_update = current_time
    
    def get_recommendation_stats(self) -> Dict:
        return {
            'authority_scores_count': len(self.authority_scores),
            'last_authority_update': self.last_authority_update,
            'weights': self.weights,
            'cache_stats': self.cache_manager.get_stats()
        }

class RecommendationAnalytics:
    
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
        self.recommendation_logs.append({
            'user_id': user_id,
            'recommendations': [(rec.item_id, rec.item_type, rec.score) for rec in recommendations],
            'generation_time': generation_time,
            'timestamp': time.time()
        })
        
        if self.recommendation_logs:
            avg_time = sum(log['generation_time'] for log in self.recommendation_logs[-100:]) / len(self.recommendation_logs[-100:])
            self.performance_metrics['avg_generation_time'] = avg_time
    
    def log_interaction(self, user_id: str, item_id: str, interaction_type: str) -> None:
        if user_id not in self.user_interactions:
            self.user_interactions[user_id] = []
        
        self.user_interactions[user_id].append({
            'item_id': item_id,
            'interaction_type': interaction_type,
            'timestamp': time.time()
        })
    
    def calculate_ctr(self, user_id: str) -> float:
        if user_id not in self.user_interactions:
            return 0.0
        
        interactions = self.user_interactions[user_id]
        clicks = sum(1 for i in interactions if i['interaction_type'] in ['click', 'save'])
        
        user_recommendations = [log for log in self.recommendation_logs if log['user_id'] == user_id]
        total_recommendations = sum(len(log['recommendations']) for log in user_recommendations)
        
        if total_recommendations == 0:
            return 0.0
        
        return clicks / total_recommendations
    
    def get_analytics_report(self) -> Dict:
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
