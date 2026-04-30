"""
Tree Data Structure Implementation for Pinterest Clone
Handles database indexes, range queries, and board hierarchy organization
"""

from typing import Any, Dict, List, Optional, Tuple, Iterator
from dataclasses import dataclass
from datetime import datetime
import bisect

@dataclass
class TreeNode:
    """Generic tree node"""
    key: Any
    value: Any
    left: Optional['TreeNode'] = None
    right: Optional['TreeNode'] = None
    height: int = 1  # For AVL tree balance
    parent: Optional['TreeNode'] = None

@dataclass
class BoardNode:
    """Board hierarchy node"""
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
    """AVL Tree implementation for database indexing"""
    
    def __init__(self):
        self.root = None
        self.size = 0
    
    def insert(self, key: Any, value: Any) -> None:
        """Insert key-value pair"""
        self.root = self._insert(self.root, key, value)
        self.size += 1
    
    def _insert(self, node: Optional[TreeNode], key: Any, value: Any) -> TreeNode:
        """Recursive insert with AVL balancing"""
        if node is None:
            return TreeNode(key, value)
        
        if key < node.key:
            node.left = self._insert(node.left, key, value)
            node.left.parent = node
        elif key > node.key:
            node.right = self._insert(node.right, key, value)
            node.right.parent = node
        else:
            # Update existing key
            node.value = value
            return node
        
        # Update height
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        
        # Balance the tree
        balance = self._get_balance(node)
        
        # Left Left Case
        if balance > 1 and key < node.left.key:
            return self._right_rotate(node)
        
        # Right Right Case
        if balance < -1 and key > node.right.key:
            return self._left_rotate(node)
        
        # Left Right Case
        if balance > 1 and key > node.left.key:
            node.left = self._left_rotate(node.left)
            return self._right_rotate(node)
        
        # Right Left Case
        if balance < -1 and key < node.right.key:
            node.right = self._right_rotate(node.right)
            return self._left_rotate(node)
        
        return node
    
    def _get_height(self, node: Optional[TreeNode]) -> int:
        """Get node height"""
        return node.height if node else 0
    
    def _get_balance(self, node: Optional[TreeNode]) -> int:
        """Get balance factor"""
        if not node:
            return 0
        return self._get_height(node.left) - self._get_height(node.right)
    
    def _right_rotate(self, y: TreeNode) -> TreeNode:
        """Right rotation"""
        x = y.left
        T2 = x.right
        
        # Perform rotation
        x.right = y
        y.left = T2
        
        # Update parents
        if T2:
            T2.parent = y
        x.parent = y.parent
        y.parent = x
        
        # Update heights
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))
        x.height = 1 + max(self._get_height(x.left), self._get_height(x.right))
        
        return x
    
    def _left_rotate(self, x: TreeNode) -> TreeNode:
        """Left rotation"""
        y = x.right
        T2 = y.left
        
        # Perform rotation
        y.left = x
        x.right = T2
        
        # Update parents
        if T2:
            T2.parent = x
        y.parent = x.parent
        x.parent = y
        
        # Update heights
        x.height = 1 + max(self._get_height(x.left), self._get_height(x.right))
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))
        
        return y
    
    def search(self, key: Any) -> Optional[Any]:
        """Search for key"""
        node = self._search(self.root, key)
        return node.value if node else None
    
    def _search(self, node: Optional[TreeNode], key: Any) -> Optional[TreeNode]:
        """Recursive search"""
        if node is None or node.key == key:
            return node
        
        if key < node.key:
            return self._search(node.left, key)
        else:
            return self._search(node.right, key)
    
    def range_query(self, start_key: Any, end_key: Any) -> List[Tuple[Any, Any]]:
        """Get all key-value pairs in range [start_key, end_key]"""
        result = []
        self._inorder_range(self.root, start_key, end_key, result)
        return result
    
    def _inorder_range(self, node: Optional[TreeNode], start_key: Any, end_key: Any, result: List) -> None:
        """Inorder traversal for range query"""
        if node is None:
            return
        
        # Visit left subtree if it might contain values in range
        if node.key > start_key:
            self._inorder_range(node.left, start_key, end_key, result)
        
        # Visit current node if in range
        if start_key <= node.key <= end_key:
            result.append((node.key, node.value))
        
        # Visit right subtree if it might contain values in range
        if node.key < end_key:
            self._inorder_range(node.right, start_key, end_key, result)
    
    def delete(self, key: Any) -> bool:
        """Delete key"""
        if self.search(key) is None:
            return False
        
        self.root = self._delete(self.root, key)
        self.size -= 1
        return True
    
    def _delete(self, node: Optional[TreeNode], key: Any) -> Optional[TreeNode]:
        """Recursive delete with AVL balancing"""
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
                # Node with two children: get inorder successor
                successor = self._get_min_node(node.right)
                node.key = successor.key
                node.value = successor.value
                node.right = self._delete(node.right, successor.key)
        
        # Update height
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        
        # Balance the tree
        balance = self._get_balance(node)
        
        # Left Left Case
        if balance > 1 and self._get_balance(node.left) >= 0:
            return self._right_rotate(node)
        
        # Left Right Case
        if balance > 1 and self._get_balance(node.left) < 0:
            node.left = self._left_rotate(node.left)
            return self._right_rotate(node)
        
        # Right Right Case
        if balance < -1 and self._get_balance(node.right) <= 0:
            return self._left_rotate(node)
        
        # Right Left Case
        if balance < -1 and self._get_balance(node.right) > 0:
            node.right = self._right_rotate(node.right)
            return self._left_rotate(node)
        
        return node
    
    def _get_min_node(self, node: TreeNode) -> TreeNode:
        """Get minimum node in subtree"""
        current = node
        while current.left:
            current = current.left
        return current
    
    def inorder_traversal(self) -> List[Tuple[Any, Any]]:
        """Get all key-value pairs in order"""
        result = []
        self._inorder(self.root, result)
        return result
    
    def _inorder(self, node: Optional[TreeNode], result: List) -> None:
        """Inorder traversal"""
        if node:
            self._inorder(node.left, result)
            result.append((node.key, node.value))
            self._inorder(node.right, result)

class TimestampIndex:
    """Index for timestamp-based range queries"""
    
    def __init__(self):
        self.index = AVLTree()
        self.timestamps = []  # Sorted list of timestamps for binary search
    
    def add(self, timestamp: datetime, data: Any) -> None:
        """Add data with timestamp"""
        ts_float = timestamp.timestamp()
        self.index.insert(ts_float, data)
        bisect.insort(self.timestamps, ts_float)
    
    def get_range(self, start_time: datetime, end_time: datetime) -> List[Any]:
        """Get all data in time range"""
        start_ts = start_time.timestamp()
        end_ts = end_time.timestamp()
        
        range_results = self.index.range_query(start_ts, end_ts)
        return [value for key, value in range_results]
    
    def get_latest(self, count: int = 10) -> List[Any]:
        """Get latest N entries"""
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
        """Remove entry by timestamp"""
        ts_float = timestamp.timestamp()
        result = self.index.delete(ts_float)
        
        if result:
            index = bisect.bisect_left(self.timestamps, ts_float)
            if index < len(self.timestamps) and self.timestamps[index] == ts_float:
                self.timestamps.pop(index)
        
        return result

class BoardHierarchy:
    """Tree structure for board organization and hierarchy"""
    
    def __init__(self):
        self.boards = {}  # board_id -> BoardNode
        self.root_boards = set()  # Boards with no parent
    
    def add_board(self, board_id: str, board_name: str, parent_id: Optional[str] = None, metadata: Dict = None) -> None:
        """Add board to hierarchy"""
        board = BoardNode(board_id, board_name, parent_id, metadata=metadata)
        self.boards[board_id] = board
        
        # Update parent's children
        if parent_id and parent_id in self.boards:
            self.boards[parent_id].children.append(board_id)
        else:
            self.root_boards.add(board_id)
    
    def get_board(self, board_id: str) -> Optional[BoardNode]:
        """Get board by ID"""
        return self.boards.get(board_id)
    
    def get_children(self, board_id: str) -> List[BoardNode]:
        """Get direct children of board"""
        board = self.boards.get(board_id)
        if not board:
            return []
        
        return [self.boards[child_id] for child_id in board.children if child_id in self.boards]
    
    def get_descendants(self, board_id: str) -> List[BoardNode]:
        """Get all descendants of board"""
        descendants = []
        self._collect_descendants(board_id, descendants)
        return descendants
    
    def _collect_descendants(self, board_id: str, descendants: List[BoardNode]) -> None:
        """Recursively collect descendants"""
        children = self.get_children(board_id)
        for child in children:
            descendants.append(child)
            self._collect_descendants(child.board_id, descendants)
    
    def get_ancestors(self, board_id: str) -> List[BoardNode]:
        """Get all ancestors of board"""
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
        """Get path from root to board"""
        ancestors = self.get_ancestors(board_id)
        ancestors.reverse()  # Root to leaf
        
        board = self.boards.get(board_id)
        if board:
            ancestors.append(board)
        
        return ancestors
    
    def move_board(self, board_id: str, new_parent_id: Optional[str]) -> bool:
        """Move board to new parent"""
        board = self.boards.get(board_id)
        if not board:
            return False
        
        # Remove from current parent
        if board.parent_id:
            parent = self.boards.get(board.parent_id)
            if parent and board_id in parent.children:
                parent.children.remove(board_id)
        else:
            self.root_boards.discard(board_id)
        
        # Add to new parent
        old_parent_id = board.parent_id
        board.parent_id = new_parent_id
        
        if new_parent_id:
            new_parent = self.boards.get(new_parent_id)
            if new_parent:
                new_parent.children.append(board_id)
            else:
                # Invalid parent, make it root
                board.parent_id = None
                self.root_boards.add(board_id)
                return False
        else:
            self.root_boards.add(board_id)
        
        return True
    
    def delete_board(self, board_id: str, move_children_to_parent: bool = True) -> bool:
        """Delete board from hierarchy"""
        board = self.boards.get(board_id)
        if not board:
            return False
        
        # Handle children
        if move_children_to_parent and board.parent_id:
            parent = self.boards.get(board.parent_id)
            if parent:
                for child_id in board.children:
                    parent.children.append(child_id)
                    child = self.boards.get(child_id)
                    if child:
                        child.parent_id = board.parent_id
        else:
            # Make children root boards
            for child_id in board.children:
                child = self.boards.get(child_id)
                if child:
                    child.parent_id = None
                    self.root_boards.add(child_id)
        
        # Remove from parent
        if board.parent_id:
            parent = self.boards.get(board.parent_id)
            if parent and board_id in parent.children:
                parent.children.remove(board_id)
        else:
            self.root_boards.discard(board_id)
        
        # Delete board
        del self.boards[board_id]
        return True
    
    def get_hierarchy_stats(self) -> Dict:
        """Get hierarchy statistics"""
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
    """Unified index management for Pinterest database operations"""
    
    def __init__(self):
        self.pin_id_index = AVLTree()  # pin_id -> pin_data
        self.user_id_index = AVLTree()  # user_id -> user_data
        self.timestamp_index = TimestampIndex()  # For activity logs
        self.board_hierarchy = BoardHierarchy()
        self.custom_indexes = {}  # index_name -> AVLTree
    
    def create_index(self, index_name: str, key_type: str = "string") -> None:
        """Create custom index"""
        if index_name not in self.custom_indexes:
            self.custom_indexes[index_name] = AVLTree()
    
    def index_pin(self, pin_id: str, pin_data: Dict) -> None:
        """Index pin by ID"""
        self.pin_id_index.insert(pin_id, pin_data)
        
        # Index by creation timestamp
        if 'created_at' in pin_data:
            created_at = pin_data['created_at']
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            self.timestamp_index.add(created_at, pin_data)
    
    def index_user(self, user_id: str, user_data: Dict) -> None:
        """Index user by ID"""
        self.user_id_index.insert(user_id, user_data)
    
    def get_pin(self, pin_id: str) -> Optional[Dict]:
        """Get pin by ID"""
        return self.pin_id_index.search(pin_id)
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        return self.user_id_index.search(user_id)
    
    def get_pins_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get pins created in date range"""
        return self.timestamp_index.get_range(start_date, end_date)
    
    def get_latest_pins(self, count: int = 10) -> List[Dict]:
        """Get latest pins"""
        return self.timestamp_index.get_latest(count)
    
    def add_to_custom_index(self, index_name: str, key: Any, value: Any) -> None:
        """Add entry to custom index"""
        if index_name not in self.custom_indexes:
            self.create_index(index_name)
        
        self.custom_indexes[index_name].insert(key, value)
    
    def query_custom_index(self, index_name: str, key: Any) -> Optional[Any]:
        """Query custom index"""
        if index_name in self.custom_indexes:
            return self.custom_indexes[index_name].search(key)
        return None
    
    def range_query_custom_index(self, index_name: str, start_key: Any, end_key: Any) -> List[Tuple[Any, Any]]:
        """Range query on custom index"""
        if index_name in self.custom_indexes:
            return self.custom_indexes[index_name].range_query(start_key, end_key)
        return []
    
    def remove_pin(self, pin_id: str) -> bool:
        """Remove pin from indexes"""
        pin_data = self.get_pin(pin_id)
        if not pin_data:
            return False
        
        # Remove from main index
        self.pin_id_index.delete(pin_id)
        
        # Remove from timestamp index
        if 'created_at' in pin_data:
            created_at = pin_data['created_at']
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            self.timestamp_index.remove(created_at)
        
        # Remove from custom indexes
        for index_tree in self.custom_indexes.values():
            # This is simplified - in production, maintain reverse mappings
            pass
        
        return True
    
    def get_index_stats(self) -> Dict:
        """Get comprehensive index statistics"""
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
