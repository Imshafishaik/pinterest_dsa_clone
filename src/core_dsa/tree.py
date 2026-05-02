from typing import Any, Dict, List, Optional, Tuple, Iterator
from dataclasses import dataclass
from datetime import datetime
import bisect

@dataclass
class TreeNode:
    key: Any
    value: Any
    left: Optional['TreeNode'] = None
    right: Optional['TreeNode'] = None
    height: int = 1
    parent: Optional['TreeNode'] = None

@dataclass
class BoardNode:
    board_id: str
    board_name: str
    parent_id: Optional[str] = None
    children: List[str] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.metadata is None:
            self.metadata = {}

class AVLTree:
    
    def __init__(self):
        self.root = None
        self.size = 0
    
    def insert(self, key: Any, value: Any) -> None:
        self.root = self._insert(self.root, key, value)
        self.size += 1
    
    def _insert(self, node: Optional[TreeNode], key: Any, value: Any) -> TreeNode:
        if node is None:
            return TreeNode(key, value)
        
        if key < node.key:
            node.left = self._insert(node.left, key, value)
            node.left.parent = node
        elif key > node.key:
            node.right = self._insert(node.right, key, value)
            node.right.parent = node
        else:
            node.value = value
            return node
        
        # Update height
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        
        # Balance the tree
        balance = self._get_balance(node)
        
        if balance > 1 and key < node.left.key:
            return self._right_rotate(node)
        
        if balance < -1 and key > node.right.key:
            return self._left_rotate(node)
        
        if balance > 1 and key > node.left.key:
            node.left = self._left_rotate(node.left)
            return self._right_rotate(node)
        
        if balance < -1 and key < node.right.key:
            node.right = self._right_rotate(node.right)
            return self._left_rotate(node)
        
        return node
    
    def _get_height(self, node: Optional[TreeNode]) -> int:
        return node.height if node else 0
    
    def _get_balance(self, node: Optional[TreeNode]) -> int:
        if not node:
            return 0
        return self._get_height(node.left) - self._get_height(node.right)
    
    def _right_rotate(self, y: TreeNode) -> TreeNode:
        x = y.left
        T2 = x.right
        
        x.right = y
        y.left = T2
        
        # Update parents
        if T2:
            T2.parent = y
        x.parent = y.parent
        y.parent = x
        
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))
        x.height = 1 + max(self._get_height(x.left), self._get_height(x.right))
        
        return x
    
    def _left_rotate(self, x: TreeNode) -> TreeNode:
        y = x.right
        T2 = y.left
        
        y.left = x
        x.right = T2
        
        # Update parents
        if T2:
            T2.parent = x
        y.parent = x.parent
        x.parent = y
        
        x.height = 1 + max(self._get_height(x.left), self._get_height(x.right))
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))
        
        return y
    
    def search(self, key: Any) -> Optional[Any]:
        node = self._search(self.root, key)
        return node.value if node else None
    
    def _search(self, node: Optional[TreeNode], key: Any) -> Optional[TreeNode]:
        if node is None or node.key == key:
            return node
        
        if key < node.key:
            return self._search(node.left, key)
        else:
            return self._search(node.right, key)
    
    def range_query(self, start_key: Any, end_key: Any) -> List[Tuple[Any, Any]]:
        result = []
        self._inorder_range(self.root, start_key, end_key, result)
        return result
    
    def _inorder_range(self, node: Optional[TreeNode], start_key: Any, end_key: Any, result: List) -> None:
        """Inorder traversal for range query"""
        if node is None:
            return
        
        if node.key > start_key:
            self._inorder_range(node.left, start_key, end_key, result)
        
        if start_key <= node.key <= end_key:
            result.append((node.key, node.value))
        
        if node.key < end_key:
            self._inorder_range(node.right, start_key, end_key, result)
    
    def delete(self, key: Any) -> bool:
        if self.search(key) is None:
            return False
        
        self.root = self._delete(self.root, key)
        self.size -= 1
        return True
    
    def _delete(self, node: Optional[TreeNode], key: Any) -> Optional[TreeNode]:
        if node is None:
            return None
        
        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            # Node to be deleted found
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left
            else:
                successor = self._get_min_node(node.right)
                node.key = successor.key
                node.value = successor.value
                node.right = self._delete(node.right, successor.key)
        
        # Update height
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        
        # Balance the tree
        balance = self._get_balance(node)
        
        if balance > 1 and self._get_balance(node.left) >= 0:
            return self._right_rotate(node)
        
        if balance > 1 and self._get_balance(node.left) < 0:
            node.left = self._left_rotate(node.left)
            return self._right_rotate(node)
        
        if balance < -1 and self._get_balance(node.right) <= 0:
            return self._left_rotate(node)
        
        if balance < -1 and self._get_balance(node.right) > 0:
            node.right = self._right_rotate(node.right)
            return self._left_rotate(node)
        
        return node
    
    def _get_min_node(self, node: TreeNode) -> TreeNode:
        current = node
        while current.left:
            current = current.left
        return current
    
    def inorder_traversal(self) -> List[Tuple[Any, Any]]:
        result = []
        self._inorder(self.root, result)
        return result
    
    def _inorder(self, node: Optional[TreeNode], result: List) -> None:
        if node:
            self._inorder(node.left, result)
            result.append((node.key, node.value))
            self._inorder(node.right, result)

class TimestampIndex:
    
    def __init__(self):
        self.index = AVLTree()
        self.timestamps = []
    
    def add(self, timestamp: datetime, data: Any) -> None:
        ts_float = timestamp.timestamp()
        self.index.insert(ts_float, data)
        bisect.insort(self.timestamps, ts_float)
    
    def get_range(self, start_time: datetime, end_time: datetime) -> List[Any]:
        start_ts = start_time.timestamp()
        end_ts = end_time.timestamp()
        
        range_results = self.index.range_query(start_ts, end_ts)
        return [value for key, value in range_results]
    
    def get_latest(self, count: int = 10) -> List[Any]:
        if not self.timestamps:
            return []
        
        latest_timestamps = self.timestamps[-count:]
        results = []
        
        for ts in latest_timestamps:
            data = self.index.search(ts)
            if data:
                results.append(data)
        
        return results
    
    def remove(self, timestamp: datetime) -> bool:
        ts_float = timestamp.timestamp()
        result = self.index.delete(ts_float)
        
        if result:
            index = bisect.bisect_left(self.timestamps, ts_float)
            if index < len(self.timestamps) and self.timestamps[index] == ts_float:
                self.timestamps.pop(index)
        
        return result

class BoardHierarchy:
    
    def __init__(self):
        self.boards = {}
    
    def add_board(self, board_id: str, board_name: str, parent_id: Optional[str] = None, metadata: Dict = None) -> None:
        board = BoardNode(board_id, board_name, parent_id, metadata=metadata)
        self.boards[board_id] = board
        
        if parent_id and parent_id in self.boards:
            self.boards[parent_id].children.append(board_id)
        else:
            self.root_boards.add(board_id)
    
    def get_board(self, board_id: str) -> Optional[BoardNode]:
        return self.boards.get(board_id)
    
    def get_children(self, board_id: str) -> List[BoardNode]:
        board = self.boards.get(board_id)
        if not board:
            return []
        
        return [self.boards[child_id] for child_id in board.children if child_id in self.boards]
    
    def get_descendants(self, board_id: str) -> List[BoardNode]:
        descendants = []
        self._collect_descendants(board_id, descendants)
        return descendants
    
    def _collect_descendants(self, board_id: str, descendants: List[BoardNode]) -> None:
        children = self.get_children(board_id)
        for child in children:
            descendants.append(child)
            self._collect_descendants(child.board_id, descendants)
    
    def get_ancestors(self, board_id: str) -> List[BoardNode]:
        ancestors = []
        current_id = board_id
        
        while current_id:
            board = self.boards.get(current_id)
            if not board:
                break
            
            if board.parent_id:
                parent = self.boards.get(board.parent_id)
                if parent:
                    ancestors.append(parent)
                    current_id = board.parent_id
                else:
                    break
            else:
                break
        
        return ancestors
    
    def get_root_path(self, board_id: str) -> List[BoardNode]:
        ancestors = self.get_ancestors(board_id)
        ancestors.reverse()
        
        board = self.boards.get(board_id)
        if board:
            ancestors.append(board)
        
        return ancestors
    
    def move_board(self, board_id: str, new_parent_id: Optional[str]) -> bool:
        board = self.boards.get(board_id)
        if not board:
            return False
        
        if board.parent_id:
            parent = self.boards.get(board.parent_id)
            if parent and board_id in parent.children:
                parent.children.remove(board_id)
        else:
            self.root_boards.discard(board_id)
        
        old_parent_id = board.parent_id
        board.parent_id = new_parent_id
        
        if new_parent_id:
            new_parent = self.boards.get(new_parent_id)
            if new_parent:
                new_parent.children.append(board_id)
            else:
                board.parent_id = None
                self.root_boards.add(board_id)
                return False
        else:
            self.root_boards.add(board_id)
        
        return True
    
    def delete_board(self, board_id: str, move_children_to_parent: bool = True) -> bool:
        board = self.boards.get(board_id)
        if not board:
            return False
        
        if move_children_to_parent and board.parent_id:
            parent = self.boards.get(board.parent_id)
            if parent:
                for child_id in board.children:
                    parent.children.append(child_id)
                    child = self.boards.get(child_id)
                    if child:
                        child.parent_id = board.parent_id
        else:
            for child_id in board.children:
                child = self.boards.get(child_id)
                if child:
                    child.parent_id = None
                    self.root_boards.add(child_id)
        
        if board.parent_id:
            parent = self.boards.get(board.parent_id)
            if parent and board_id in parent.children:
                parent.children.remove(board_id)
        else:
            self.root_boards.discard(board_id)
        
        del self.boards[board_id]
        return True
    
    def get_hierarchy_stats(self) -> Dict:
        total_boards = len(self.boards)
        max_depth = 0
        leaf_count = 0
        
        for board_id in self.boards:
            depth = len(self.get_root_path(board_id)) - 1
            max_depth = max(max_depth, depth)
            
            board = self.boards[board_id]
            if not board.children:
                leaf_count += 1
        
        return {
            'total_boards': total_boards,
            'root_boards': len(self.root_boards),
            'max_depth': max_depth,
            'leaf_boards': leaf_count,
            'avg_depth': sum(len(self.get_root_path(bid)) - 1 for bid in self.boards) / total_boards if total_boards > 0 else 0
        }

class DatabaseIndexManager:
    
    def __init__(self):
        self.pin_id_index = AVLTree()
        self.user_id_index = AVLTree()
        self.timestamp_index = TimestampIndex()
        self.board_hierarchy = BoardHierarchy()
        self.custom_indexes = {}
    
    def create_index(self, index_name: str, key_type: str = "string") -> None:
        if index_name not in self.custom_indexes:
            self.custom_indexes[index_name] = AVLTree()
    
    def index_pin(self, pin_id: str, pin_data: Dict) -> None:
        self.pin_id_index.insert(pin_id, pin_data)
        
        if 'created_at' in pin_data:
            created_at = pin_data['created_at']
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            self.timestamp_index.add(created_at, pin_data)
    
    def index_user(self, user_id: str, user_data: Dict) -> None:
        self.user_id_index.insert(user_id, user_data)
    
    def get_pin(self, pin_id: str) -> Optional[Dict]:
        return self.pin_id_index.search(pin_id)
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        return self.user_id_index.search(user_id)
    
    def get_pins_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        return self.timestamp_index.get_range(start_date, end_date)
    
    def get_latest_pins(self, count: int = 10) -> List[Dict]:
        return self.timestamp_index.get_latest(count)
    
    def add_to_custom_index(self, index_name: str, key: Any, value: Any) -> None:
        if index_name not in self.custom_indexes:
            self.create_index(index_name)
        
        self.custom_indexes[index_name].insert(key, value)
    
    def query_custom_index(self, index_name: str, key: Any) -> Optional[Any]:
        if index_name in self.custom_indexes:
            return self.custom_indexes[index_name].search(key)
        return None
    
    def range_query_custom_index(self, index_name: str, start_key: Any, end_key: Any) -> List[Tuple[Any, Any]]:
        if index_name in self.custom_indexes:
            return self.custom_indexes[index_name].range_query(start_key, end_key)
        return []
    
    def remove_pin(self, pin_id: str) -> bool:
        pin_data = self.get_pin(pin_id)
        if not pin_data:
            return False
        
        self.pin_id_index.delete(pin_id)
        
        if 'created_at' in pin_data:
            created_at = pin_data['created_at']
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            self.timestamp_index.remove(created_at)
        
        for index_tree in self.custom_indexes.values():
            pass
        
        return True
    
    def get_index_stats(self) -> Dict:
        return {
            'pin_index': {
                'size': self.pin_id_index.size,
                'height': self.pin_id_index.root.height if self.pin_id_index.root else 0
            },
            'user_index': {
                'size': self.user_id_index.size,
                'height': self.user_id_index.root.height if self.user_id_index.root else 0
            },
            'timestamp_index': {
                'entries': len(self.timestamp_index.timestamps),
                'time_span': (self.timestamp_index.timestamps[0], self.timestamp_index.timestamps[-1]) if self.timestamp_index.timestamps else None
            },
            'board_hierarchy': self.board_hierarchy.get_hierarchy_stats(),
            'custom_indexes': {
                name: tree.size for name, tree in self.custom_indexes.items()
            }
        }
