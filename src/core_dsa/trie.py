from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import heapq

class TrieNode:
    
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.frequency = 0
        self.data = None
        self.completions_heap = []

class PinterestTrie:
    
    def __init__(self, max_completions: int = 10):
        self.root = TrieNode()
        self.max_completions = max_completions
        self.word_frequency = defaultdict(int)
        
    def insert(self, word: str, data: Dict = None, frequency: int = 1) -> None:
        if not word:
            return
            
        word = word.lower().strip()
        node = self.root
        
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        node.is_end_of_word = True
        node.frequency += frequency
        node.data = data
        self.word_frequency[word] += frequency
        
        self._update_completion_heap(self.root, word, frequency)
    
    def _update_completion_heap(self, start_node: TrieNode, word: str, frequency: int) -> None:
        current = start_node
        
        for char in word:
            current = current.children[char]
            found = False
            
            for i, (freq, heap_word) in enumerate(current.completions_heap):
                if heap_word == word:
                    current.completions_heap[i] = (frequency, word)
                    found = True
                    heapq.heapify(current.completions_heap)
                    break
            
            if not found:
                if len(current.completions_heap) < self.max_completions:
                    heapq.heappush(current.completions_heap, (frequency, word))
                elif frequency > current.completions_heap[0][0]:
                    heapq.heapreplace(current.completions_heap, (frequency, word))
    
    def search(self, word: str) -> Optional[TrieNode]:
        if not word:
            return None
            
        word = word.lower().strip()
        node = self.root
        
        for char in word:
            if char not in node.children:
                return None
            node = node.children[char]
        
        return node if node.is_end_of_word else None
    
    def starts_with(self, prefix: str) -> List[str]:
        if not prefix:
            return []
            
        prefix = prefix.lower().strip()
        node = self.root
        
        # Navigate to prefix node
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        words = []
        self._collect_words(node, prefix, words)
        return words
    
    def _collect_words(self, node: TrieNode, prefix: str, words: List[str]) -> None:
        if node.is_end_of_word:
            words.append(prefix)
        
        for char, child_node in node.children.items():
            self._collect_words(child_node, prefix + char, words)
    
    def get_autocomplete_completions(self, prefix: str, k: int = 10) -> List[Dict]:
        if not prefix:
            return []
            
        prefix = prefix.lower().strip()
        node = self.root
        
        # Navigate to prefix node
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        completions = sorted(node.completions_heap, key=lambda x: x[0], reverse=True)
        
        result = []
        for freq, word in completions[:k]:
            word_node = self.search(word)
            result.append({
                'word': word,
                'frequency': freq,
                'data': word_node.data if word_node else None
            })
        
        return result
    
    def get_prefix_matches_with_scores(self, prefix: str, k: int = 10) -> List[Tuple[str, float]]:
        if not prefix:
            return []
        
        matches = self.starts_with(prefix)
        prefix_len = len(prefix)
        
        scored_matches = []
        for word in matches:
            frequency = self.word_frequency[word]
            
            if word.startswith(prefix):
                prefix_factor = 1.0
            else:
                prefix_factor = 0.5
            
            score = frequency * prefix_factor
            scored_matches.append((word, score))
        
        scored_matches.sort(key=lambda x: x[1], reverse=True)
        return scored_matches[:k]
    
    def delete(self, word: str) -> bool:
        if not word:
            return False
            
        word = word.lower().strip()
        
        def _delete_helper(node: TrieNode, word: str, depth: int) -> bool:
            if depth == len(word):
                if not node.is_end_of_word:
                    return False
                
                node.is_end_of_word = False
                node.frequency = 0
                node.data = None
                
                return len(node.children) == 0
            
            char = word[depth]
            child_node = node.children.get(char)
            
            if not child_node:
                return False
            
            should_delete_child = _delete_helper(child_node, word, depth + 1)
            
            if should_delete_child:
                del node.children[char]
                return len(node.children) == 0 and not node.is_end_of_word
            
            return False
        
        result = _delete_helper(self.root, word, 0)
        if result:
            self.word_frequency[word] = 0
        return result
    
    def get_all_words(self) -> List[str]:
        words = []
        self._collect_words(self.root, "", words)
        return words
    
    def get_statistics(self) -> Dict:
        total_words = len([w for w in self.word_frequency.keys() if self.word_frequency[w] > 0])
        total_nodes = self._count_nodes(self.root)
        
        return {
            'total_words': total_words,
            'total_nodes': total_nodes,
            'max_depth': self._get_max_depth(self.root),
            'avg_frequency': sum(self.word_frequency.values()) / total_words if total_words > 0 else 0
        }
    
    def _count_nodes(self, node: TrieNode) -> int:
        count = 1
        for child in node.children.values():
            count += self._count_nodes(child)
        return count
    
    def _get_max_depth(self, node: TrieNode, depth: int = 0) -> int:
        if not node.children:
            return depth
        
        max_child_depth = 0
        for child in node.children.values():
            child_depth = self._get_max_depth(child, depth + 1)
            max_child_depth = max(max_child_depth, child_depth)
        
        return max_child_depth

class TagIndexer:
    
    def __init__(self):
        self.tag_trie = PinterestTrie(max_completions=20)
        self.pin_tags = defaultdict(set)
        self.tag_pins = defaultdict(set)
    
    def add_tags_to_pin(self, pin_id: str, tags: List[str]) -> None:
        for tag in tags:
            tag = tag.lower().strip()
            if tag:
                self.tag_trie.insert(tag, {'pin_ids': list(self.tag_pins[tag])})
                self.pin_tags[pin_id].add(tag)
                self.tag_pins[tag].add(pin_id)
    
    def get_pins_by_tag(self, tag: str) -> List[str]:
        tag = tag.lower().strip()
        return list(self.tag_pins.get(tag, set()))
    
    def get_tags_by_prefix(self, prefix: str, k: int = 10) -> List[Dict]:
        completions = self.tag_trie.get_autocomplete_completions(prefix, k)
        
        result = []
        for completion in completions:
            tag = completion['word']
            pin_count = len(self.tag_pins.get(tag, set()))
            result.append({
                'tag': tag,
                'pin_count': pin_count,
                'frequency': completion['frequency']
            })
        
        return result
    
    def get_related_tags(self, tag: str, k: int = 5) -> List[str]:
        tag = tag.lower().strip()
        pins_with_tag = self.tag_pins.get(tag, set())
        
        co_tag_counts = defaultdict(int)
        for pin_id in pins_with_tag:
            for co_tag in self.pin_tags.get(pin_id, set()):
                if co_tag != tag:
                    co_tag_counts[co_tag] += 1
        
        related_tags = sorted(co_tag_counts.items(), key=lambda x: x[1], reverse=True)
        return [tag for tag, count in related_tags[:k]]
    
    def remove_tags_from_pin(self, pin_id: str, tags: List[str]) -> None:
        for tag in tags:
            tag = tag.lower().strip()
            if tag in self.pin_tags[pin_id]:
                self.pin_tags[pin_id].remove(tag)
                self.tag_pins[tag].discard(pin_id)
                
                if not self.tag_pins[tag]:
                    self.tag_trie.delete(tag)

class BoardNameIndexer:
    
    def __init__(self):
        self.board_trie = PinterestTrie(max_completions=15)
        self.board_data = {}
    
    def add_board(self, board_id: str, board_name: str, board_data: Dict = None) -> None:
        words = board_name.lower().strip().split()
        
        for word in words:
            if len(word) >= 2:
                self.board_trie.insert(word, {
                    'board_id': board_id,
                    'board_name': board_name,
                    'board_data': board_data or {}
                })
        
        self.board_trie.insert(board_name.lower().strip(), {
            'board_id': board_id,
            'board_name': board_name,
            'board_data': board_data or {}
        })
        
        self.board_data[board_id] = {
            'name': board_name,
            'data': board_data or {}
        }
    
    def search_boards(self, query: str, k: int = 10) -> List[Dict]:
        matches = self.board_trie.get_prefix_matches_with_scores(query, k)
        
        result = []
        seen_boards = set()
        
        for word, score in matches:
            completions = self.board_trie.get_autocomplete_completions(word, 5)
            
            for completion in completions:
                board_data = completion['data']
                if board_data and board_data['board_id'] not in seen_boards:
                    result.append({
                        'board_id': board_data['board_id'],
                        'board_name': board_data['board_name'],
                        'board_data': board_data['board_data'],
                        'relevance_score': score
                    })
                    seen_boards.add(board_data['board_id'])
                    
                    if len(result) >= k:
                        break
            
            if len(result) >= k:
                break
        
        return result
    
    def get_board_suggestions(self, partial_name: str, k: int = 5) -> List[str]:
        completions = self.board_trie.get_autocomplete_completions(partial_name, k)
        return [comp['word'] for comp in completions]

class PinterestSearchIndex:
    
    def __init__(self):
        self.tag_indexer = TagIndexer()
        self.board_indexer = BoardNameIndexer()
        self.pin_content_trie = PinterestTrie(max_completions=30)
    
    def index_pin(self, pin_id: str, pin_data: Dict) -> None:
        tags = pin_data.get('tags', [])
        self.tag_indexer.add_tags_to_pin(pin_id, tags)
        
        title = pin_data.get('title', '')
        description = pin_data.get('description', '')
        
        content_words = (title + ' ' + description).lower().split()
        for word in content_words:
            if len(word) >= 3:
                self.pin_content_trie.insert(word, {
                    'pin_id': pin_id,
                    'pin_data': pin_data
                })
    
    def index_board(self, board_id: str, board_name: str, board_data: Dict = None) -> None:
        self.board_indexer.add_board(board_id, board_name, board_data)
    
    def search_pins(self, query: str, k: int = 20) -> List[Dict]:
        matches = self.pin_content_trie.get_prefix_matches_with_scores(query, k)
        
        result = []
        seen_pins = set()
        
        for word, score in matches:
            completions = self.pin_content_trie.get_autocomplete_completions(word, 10)
            
            for completion in completions:
                pin_data = completion['data']
                if pin_data and pin_data['pin_id'] not in seen_pins:
                    result.append({
                        'pin_id': pin_data['pin_id'],
                        'pin_data': pin_data['pin_data'],
                        'relevance_score': score
                    })
                    seen_pins.add(pin_data['pin_id'])
                    
                    if len(result) >= k:
                        break
            
            if len(result) >= k:
                break
        
        return result
    
    def search_by_tags(self, tags: List[str], k: int = 20) -> List[str]:
        """Search pins by tags (AND operation)"""
        if not tags:
            return []
        
        tag_pin_sets = []
        for tag in tags:
            pins = self.tag_indexer.get_pins_by_tag(tag)
            tag_pin_sets.append(set(pins))
        
            result_pins = set.intersection(*tag_pin_sets)
        else:
            result_pins = set()
        
        return list(result_pins)[:k]
    
    def get_tag_suggestions(self, prefix: str, k: int = 10) -> List[Dict]:
        return self.tag_indexer.get_tags_by_prefix(prefix, k)
    
    def get_board_suggestions(self, prefix: str, k: int = 10) -> List[Dict]:
        return self.board_indexer.search_boards(prefix, k)
    
    def get_search_suggestions(self, query: str, k: int = 10) -> List[str]:
        content_suggestions = self.pin_content_trie.get_autocomplete_completions(query, k)
        tag_suggestions = self.tag_indexer.get_tags_by_prefix(query, k)
        board_suggestions = self.board_indexer.search_boards(query, k)
        
        all_suggestions = set()
        
        for content in content_suggestions:
            all_suggestions.add(content['word'])
        
        for tag in tag_suggestions:
            all_suggestions.add(tag['tag'])
        
        for board in board_suggestions:
            all_suggestions.add(board['board_name'])
        
        return list(all_suggestions)[:k]
    
    def get_index_stats(self) -> Dict:
        return {
            'tag_index': {
                'total_tags': len(self.tag_indexer.tag_pins),
                'tag_trie_stats': self.tag_indexer.tag_trie.get_statistics()
            },
            'board_index': {
                'total_boards': len(self.board_indexer.board_data),
                'board_trie_stats': self.board_indexer.board_trie.get_statistics()
            },
            'content_index': {
                'content_trie_stats': self.pin_content_trie.get_statistics()
            }
        }
