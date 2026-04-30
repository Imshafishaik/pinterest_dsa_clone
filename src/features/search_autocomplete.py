"""
Search Autocomplete Feature for Pinterest Clone
Implements O(m) prefix traversal using Trie data structure
"""

import time
from typing import Dict, List, Tuple, Optional
from core_dsa.trie import PinterestTrie, PinterestSearchIndex, PinterestTrie

class SearchAutocomplete:
    """Search autocomplete system with O(m) prefix traversal"""
    
    def __init__(self, search_index: PinterestSearchIndex):
        self.search_index = search_index
        self.query_history = {}  # user_id -> [queries, ...]
        self.popularity_cache = {}  # query -> popularity_score
        
    def get_autocomplete_suggestions(self, query: str, user_id: str = None, 
                                   max_suggestions: int = 10) -> List[Dict]:
        """
        Get autocomplete suggestions with O(m) prefix traversal
        Returns ranked suggestions based on frequency and user history
        """
        if not query or len(query.strip()) < 2:
            return []
        
        query = query.strip().lower()
        start_time = time.time()
        
        # Get suggestions from different sources
        content_suggestions = self._get_content_suggestions(query, max_suggestions // 2)
        tag_suggestions = self._get_tag_suggestions(query, max_suggestions // 2)
        board_suggestions = self._get_board_suggestions(query, max_suggestions // 2)
        
        # Combine and rank suggestions
        all_suggestions = []
        
        # Add content suggestions
        for suggestion in content_suggestions:
            all_suggestions.append({
                'type': 'content',
                'text': suggestion['word'],
                'frequency': suggestion['frequency'],
                'data': suggestion['data'],
                'relevance_score': self._calculate_relevance_score(query, suggestion['word'], suggestion['frequency'])
            })
        
        # Add tag suggestions
        for suggestion in tag_suggestions:
            all_suggestions.append({
                'type': 'tag',
                'text': suggestion['tag'],
                'frequency': suggestion['frequency'],
                'pin_count': suggestion['pin_count'],
                'relevance_score': self._calculate_relevance_score(query, suggestion['tag'], suggestion['frequency'])
            })
        
        # Add board suggestions
        for suggestion in board_suggestions:
            all_suggestions.append({
                'type': 'board',
                'text': suggestion['board_name'],
                'board_id': suggestion['board_id'],
                'relevance_score': suggestion['relevance_score']
            })
        
        # Apply personalization if user_id provided
        if user_id:
            all_suggestions = self._personalize_suggestions(all_suggestions, user_id, query)
        
        # Sort by relevance score and limit
        all_suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)
        final_suggestions = all_suggestions[:max_suggestions]
        
        # Record query for learning
        self._record_query(user_id, query)
        
        # Log performance
        traversal_time = time.time() - start_time
        
        return {
            'suggestions': final_suggestions,
            'query': query,
            'traversal_time_ms': traversal_time * 1000,
            'total_suggestions': len(final_suggestions)
        }
    
    def _get_content_suggestions(self, query: str, limit: int) -> List[Dict]:
        """Get content suggestions from pin titles/descriptions"""
        completions = self.search_index.pin_content_trie.get_autocomplete_completions(query, limit)
        return completions
    
    def _get_tag_suggestions(self, query: str, limit: int) -> List[Dict]:
        """Get tag suggestions"""
        return self.search_index.get_tag_suggestions(query, limit)
    
    def _get_board_suggestions(self, query: str, limit: int) -> List[Dict]:
        """Get board suggestions"""
        return self.search_index.search_boards(query, limit)
    
    def _calculate_relevance_score(self, query: str, suggestion: str, frequency: int) -> float:
        """Calculate relevance score for suggestion"""
        # Exact match gets highest score
        if suggestion == query:
            base_score = 1.0
        # Prefix match gets high score
        elif suggestion.startswith(query):
            base_score = 0.8
        # Contains query gets medium score
        elif query in suggestion:
            base_score = 0.6
        else:
            base_score = 0.3
        
        # Factor in frequency (logarithmic scaling)
        frequency_score = min(frequency / 1000.0, 1.0) if frequency > 0 else 0.0
        
        # Factor in length (shorter suggestions preferred)
        length_score = max(0, 1.0 - len(suggestion) / 50.0)
        
        # Combined score
        relevance_score = (base_score * 0.5 + frequency_score * 0.3 + length_score * 0.2)
        
        return relevance_score
    
    def _personalize_suggestions(self, suggestions: List[Dict], user_id: str, query: str) -> List[Dict]:
        """Personalize suggestions based on user history"""
        user_history = self.query_history.get(user_id, [])
        
        # Boost suggestions that match user's previous queries
        for suggestion in suggestions:
            personalization_boost = 0.0
            
            # Check if suggestion matches previous queries
            for prev_query in user_history[-10:]:  # Last 10 queries
                if suggestion['text'] in prev_query or prev_query in suggestion['text']:
                    personalization_boost += 0.1
            
            # Apply boost
            suggestion['relevance_score'] += personalization_boost
            suggestion['personalization_boost'] = personalization_boost
        
        return suggestions
    
    def _record_query(self, user_id: str, query: str) -> None:
        """Record query for learning and personalization"""
        if user_id:
            if user_id not in self.query_history:
                self.query_history[user_id] = []
            
            self.query_history[user_id].append(query)
            
            # Keep only last 50 queries per user
            if len(self.query_history[user_id]) > 50:
                self.query_history[user_id] = self.query_history[user_id][-50:]
        
        # Update global popularity
        self.popularity_cache[query] = self.popularity_cache.get(query, 0) + 1
    
    def get_trending_queries(self, limit: int = 20) -> List[Dict]:
        """Get trending search queries"""
        # Sort by popularity
        trending = sorted(self.popularity_cache.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'query': query, 'popularity': count}
            for query, count in trending[:limit]
        ]
    
    def get_user_search_history(self, user_id: str, limit: int = 20) -> List[str]:
        """Get user's search history"""
        history = self.query_history.get(user_id, [])
        return history[-limit:] if history else []
    
    def clear_user_history(self, user_id: str) -> bool:
        """Clear user's search history"""
        if user_id in self.query_history:
            del self.query_history[user_id]
            return True
        return False

class AdvancedAutocomplete:
    """Advanced autocomplete with fuzzy matching and semantic suggestions"""
    
    def __init__(self, search_index: PinterestSearchIndex):
        self.search_index = search_index
        self.base_autocomplete = SearchAutocomplete(search_index)
        
        # Common misspellings and corrections
        self.spell_corrections = {
            'recipies': 'recipes',
            'dekor': 'decor',
            'hallowen': 'halloween',
            'chrismas': 'christmas',
            'valentines': 'valentine',
            'diys': 'diy',
            'crafts': 'craft',
            'interiordesign': 'interior design'
        }
    
    def get_smart_suggestions(self, query: str, user_id: str = None, 
                           max_suggestions: int = 10) -> Dict:
        """Get smart suggestions with spell correction and fuzzy matching"""
        # First, try exact autocomplete
        exact_results = self.base_autocomplete.get_autocomplete_suggestions(
            query, user_id, max_suggestions
        )
        
        suggestions = exact_results['suggestions']
        
        # If no exact matches, try spell correction
        if len(suggestions) < 3:
            corrected_query = self._correct_spelling(query)
            if corrected_query != query:
                corrected_results = self.base_autocomplete.get_autocomplete_suggestions(
                    corrected_query, user_id, max_suggestions // 2
                )
                
                # Add corrected suggestions with note
                for suggestion in corrected_results['suggestions']:
                    suggestion['spell_corrected'] = True
                    suggestion['original_query'] = query
                    suggestion['corrected_query'] = corrected_query
                    suggestions.extend(corrected_results['suggestions'])
        
        # If still few results, try fuzzy matching
        if len(suggestions) < 3:
            fuzzy_results = self._get_fuzzy_suggestions(query, max_suggestions // 2)
            suggestions.extend(fuzzy_results)
        
        # Sort and limit
        suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)
        final_suggestions = suggestions[:max_suggestions]
        
        return {
            'suggestions': final_suggestions,
            'query': query,
            'spell_corrected': any(s.get('spell_corrected', False) for s in final_suggestions),
            'fuzzy_matched': any(s.get('fuzzy_matched', False) for s in final_suggestions),
            'total_suggestions': len(final_suggestions)
        }
    
    def _correct_spelling(self, query: str) -> str:
        """Correct common spelling mistakes"""
        corrected = query.lower()
        
        for mistake, correction in self.spell_corrections.items():
            if mistake in corrected:
                corrected = corrected.replace(mistake, correction)
        
        return corrected
    
    def _get_fuzzy_suggestions(self, query: str, limit: int) -> List[Dict]:
        """Get fuzzy matching suggestions"""
        # Get all words from trie
        all_words = self.search_index.pin_content_trie.get_all_words()
        
        fuzzy_matches = []
        
        for word in all_words[:1000]:  # Limit for performance
            # Simple Levenshtein distance approximation
            if self._is_fuzzy_match(query, word):
                frequency = self.search_index.pin_content_trie.word_frequency.get(word, 0)
                
                fuzzy_matches.append({
                    'type': 'content',
                    'text': word,
                    'frequency': frequency,
                    'relevance_score': self._calculate_fuzzy_score(query, word, frequency),
                    'fuzzy_matched': True
                })
        
        # Sort by fuzzy score and return top matches
        fuzzy_matches.sort(key=lambda x: x['relevance_score'], reverse=True)
        return fuzzy_matches[:limit]
    
    def _is_fuzzy_match(self, query: str, word: str, max_distance: int = 2) -> bool:
        """Check if word is fuzzy match (simplified Levenshtein)"""
        if abs(len(query) - len(word)) > max_distance:
            return False
        
        # Simple character matching check
        matches = sum(1 for i, char in enumerate(query) if i < len(word) and char == word[i])
        similarity = matches / max(len(query), len(word))
        
        return similarity >= 0.6  # 60% similarity threshold
    
    def _calculate_fuzzy_score(self, query: str, word: str, frequency: int) -> float:
        """Calculate fuzzy match score"""
        # Length similarity
        length_similarity = 1.0 - abs(len(query) - len(word)) / max(len(query), len(word))
        
        # Character similarity
        matches = sum(1 for i, char in enumerate(query) if i < len(word) and char == word[i])
        char_similarity = matches / max(len(query), len(word))
        
        # Frequency score
        freq_score = min(frequency / 100.0, 1.0) if frequency > 0 else 0.0
        
        # Combined fuzzy score
        fuzzy_score = (length_similarity * 0.3 + char_similarity * 0.4 + freq_score * 0.3)
        
        return fuzzy_score

class AutocompleteAnalytics:
    """Analytics for autocomplete performance and usage"""
    
    def __init__(self):
        self.query_stats = {
            'total_queries': 0,
            'avg_suggestions_returned': 0.0,
            'avg_response_time_ms': 0.0,
            'spell_corrections': 0,
            'fuzzy_matches': 0
        }
        self.popular_queries = {}
        self.user_engagement = {}
    
    def record_query(self, query_data: Dict) -> None:
        """Record autocomplete query statistics"""
        self.query_stats['total_queries'] += 1
        
        suggestions = query_data.get('suggestions', [])
        response_time = query_data.get('traversal_time_ms', 0)
        
        # Update averages
        total_queries = self.query_stats['total_queries']
        current_avg_suggestions = self.query_stats['avg_suggestions_returned']
        current_avg_time = self.query_stats['avg_response_time_ms']
        
        self.query_stats['avg_suggestions_returned'] = (
            (current_avg_suggestions * (total_queries - 1) + len(suggestions)) / total_queries
        )
        
        self.query_stats['avg_response_time_ms'] = (
            (current_avg_time * (total_queries - 1) + response_time) / total_queries
        )
        
        # Track spell corrections and fuzzy matches
        if query_data.get('spell_corrected', False):
            self.query_stats['spell_corrections'] += 1
        
        if query_data.get('fuzzy_matched', False):
            self.query_stats['fuzzy_matches'] += 1
        
        # Track popular queries
        query = query_data.get('query', '')
        self.popular_queries[query] = self.popular_queries.get(query, 0) + 1
    
    def record_selection(self, user_id: str, selected_suggestion: Dict, query: str) -> None:
        """Record when user selects a suggestion"""
        if user_id not in self.user_engagement:
            self.user_engagement[user_id] = {
                'selections': [],
                'queries': []
            }
        
        self.user_engagement[user_id]['selections'].append({
            'suggestion': selected_suggestion,
            'query': query,
            'timestamp': time.time()
        })
    
    def get_analytics_report(self) -> Dict:
        """Get comprehensive analytics report"""
        # Calculate engagement metrics
        total_selections = sum(len(user_data['selections']) for user_data in self.user_engagement.values())
        selection_rate = total_selections / self.query_stats['total_queries'] if self.query_stats['total_queries'] > 0 else 0
        
        # Most popular queries
        popular = sorted(self.popular_queries.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'query_statistics': self.query_stats,
            'engagement_metrics': {
                'total_selections': total_selections,
                'selection_rate': selection_rate,
                'active_users': len(self.user_engagement)
            },
            'popular_queries': popular,
            'performance_metrics': {
                'avg_response_time_ms': self.query_stats['avg_response_time_ms'],
                'spell_correction_rate': self.query_stats['spell_corrections'] / self.query_stats['total_queries'] if self.query_stats['total_queries'] > 0 else 0,
                'fuzzy_match_rate': self.query_stats['fuzzy_matches'] / self.query_stats['total_queries'] if self.query_stats['total_queries'] > 0 else 0
            }
        }
