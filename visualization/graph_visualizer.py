"""
Graph Visualization Components for Pinterest Clone
Visualizes social graphs, interest graphs, and data structures using Matplotlib
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Optional, Any
import seaborn as sns
from dataclasses import dataclass
import os

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

@dataclass
class GraphLayoutConfig:
    """Configuration for graph layout"""
    layout_algorithm: str = "spring"  # spring, circular, random, shell
    node_size: int = 300
    edge_width: float = 1.0
    font_size: int = 8
    figsize: Tuple[int, int] = (12, 8)
    dpi: int = 100
    node_color_map: str = "viridis"
    edge_color: str = "gray"
    background_color: str = "white"

class SocialGraphVisualizer:
    """Visualizer for Pinterest social graphs"""
    
    def __init__(self, config: GraphLayoutConfig = None):
        self.config = config or GraphLayoutConfig()
        
    def visualize_social_graph(self, graph, save_path: str = None, show: bool = True) -> None:
        """Visualize social graph with user relationships"""
        plt.figure(figsize=self.config.figsize, dpi=self.config.dpi)
        
        # Create layout
        if self.config.layout_algorithm == "spring":
            pos = nx.spring_layout(graph.social_graph, k=2, iterations=50)
        elif self.config.layout_algorithm == "circular":
            pos = nx.circular_layout(graph.social_graph)
        elif self.config.layout_algorithm == "shell":
            pos = nx.shell_layout(graph.social_graph)
        else:
            pos = nx.random_layout(graph.social_graph)
        
        # Draw nodes with different colors based on influence
        node_colors = []
        node_sizes = []
        
        for node in graph.social_graph.nodes():
            influence = graph.get_influence_score(node)
            node_colors.append(influence)
            node_sizes.append(self.config.node_size * (1 + influence * 2))
        
        # Draw the graph
        nx.draw_networkx_nodes(
            graph.social_graph, pos, 
            node_color=node_colors,
            node_size=node_sizes,
            cmap=self.config.node_color_map,
            alpha=0.8,
            edgecolors='black',
            linewidths=1
        )
        
        nx.draw_networkx_edges(
            graph.social_graph, pos,
            edge_color=self.config.edge_color,
            width=self.config.edge_width,
            alpha=0.6,
            arrows=True,
            arrowsize=20,
            arrowstyle='->'
        )
        
        # Draw labels for important nodes
        important_nodes = [node for node in graph.social_graph.nodes() 
                         if graph.get_influence_score(node) > 0.5]
        
        if important_nodes:
            nx.draw_networkx_labels(
                graph.social_graph, pos,
                labels={node: node for node in important_nodes},
                font_size=self.config.font_size,
                font_weight='bold'
            )
        
        # Add title and legend
        plt.title("Pinterest Social Graph\n(Node size = Influence Score)", 
                 fontsize=16, fontweight='bold')
        
        # Add colorbar for influence scores
        sm = plt.cm.ScalarMappable(cmap=self.config.node_color_map, 
                                   norm=plt.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=plt.gca())
        cbar.set_label('Influence Score', rotation=270, labelpad=15)
        
        plt.axis('off')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
    
    def visualize_following_patterns(self, graph, save_path: str = None, show: bool = True) -> None:
        """Visualize following patterns and mutual connections"""
        plt.figure(figsize=self.config.figsize, dpi=self.config.dpi)
        
        # Create subgraph with only following relationships
        following_graph = graph.social_graph.copy()
        
        # Identify mutual followers
        mutual_edges = []
        for user in following_graph.nodes():
            mutual = graph.get_mutual_followers(user)
            for mutual_user in mutual:
                if following_graph.has_edge(user, mutual_user) and following_graph.has_edge(mutual_user, user):
                    mutual_edges.append((user, mutual_user))
        
        # Layout
        pos = nx.spring_layout(following_graph, k=3, iterations=50)
        
        # Draw all edges in gray
        nx.draw_networkx_edges(
            following_graph, pos,
            edge_color='lightgray',
            width=1,
            alpha=0.5,
            arrows=True,
            arrowsize=15
        )
        
        # Highlight mutual connections
        if mutual_edges:
            nx.draw_networkx_edges(
                following_graph, pos,
                edgelist=mutual_edges,
                edge_color='red',
                width=3,
                alpha=0.8,
                arrows=True,
                arrowsize=20
            )
        
        # Draw nodes
        nx.draw_networkx_nodes(
            following_graph, pos,
            node_size=self.config.node_size,
            node_color='lightblue',
            alpha=0.8,
            edgecolors='black',
            linewidths=1
        )
        
        # Draw labels
        nx.draw_networkx_labels(
            following_graph, pos,
            font_size=self.config.font_size,
            font_weight='bold'
        )
        
        plt.title("Following Patterns\n(Red edges = Mutual following)", 
                 fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()

class InterestGraphVisualizer:
    """Visualizer for Pinterest interest graphs"""
    
    def __init__(self, config: GraphLayoutConfig = None):
        self.config = config or GraphLayoutConfig()
    
    def visualize_interest_graph(self, graph, save_path: str = None, show: bool = True) -> None:
        """Visualize interest graph with pins, boards, and users"""
        plt.figure(figsize=self.config.figsize, dpi=self.config.dpi)
        
        # Create subgraph with interest connections
        interest_graph = graph.interest_graph.copy()
        
        # Color nodes by type
        node_colors = []
        for node in interest_graph.nodes():
            node_data = interest_graph.nodes[node]
            node_type = node_data.get('type', 'unknown')
            
            if node_type == 'user':
                node_colors.append('blue')
            elif node_type == 'pin':
                node_colors.append('green')
            elif node_type == 'board':
                node_colors.append('orange')
            else:
                node_colors.append('gray')
        
        # Layout
        pos = nx.spring_layout(interest_graph, k=2, iterations=50)
        
        # Draw edges
        nx.draw_networkx_edges(
            interest_graph, pos,
            edge_color=self.config.edge_color,
            width=self.config.edge_width,
            alpha=0.6
        )
        
        # Draw nodes
        nx.draw_networkx_nodes(
            interest_graph, pos,
            node_color=node_colors,
            node_size=self.config.node_size,
            alpha=0.8,
            edgecolors='black',
            linewidths=1
        )
        
        # Create legend
        legend_elements = [
            patches.Patch(color='blue', label='Users'),
            patches.Patch(color='green', label='Pins'),
            patches.Patch(color='orange', label='Boards')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        plt.title("Pinterest Interest Graph\n(Blue=Users, Green=Pins, Orange=Boards)", 
                 fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
    
    def visualize_user_interests(self, graph, user_id: str, save_path: str = None, show: bool = True) -> None:
        """Visualize specific user's interest network"""
        plt.figure(figsize=self.config.figsize, dpi=self.config.dpi)
        
        # Get user's interests
        interests = graph.dfs_explore_interests(user_id, max_depth=2)
        
        # Create subgraph with user's interests
        interest_subgraph = nx.Graph()
        
        # Add user node
        interest_subgraph.add_node(user_id, type='user')
        
        # Add interest nodes and edges
        for pin_id in interests['pins']:
            interest_subgraph.add_node(pin_id, type='pin')
            interest_subgraph.add_edge(user_id, pin_id)
        
        for board_id in interests['boards']:
            interest_subgraph.add_node(board_id, type='board')
            interest_subgraph.add_edge(user_id, board_id)
        
        # Add pin-board connections
        for pin_id in interests['pins']:
            for board_id in interests['boards']:
                # Check if pin belongs to board (simplified)
                interest_subgraph.add_edge(pin_id, board_id)
        
        # Layout
        pos = nx.spring_layout(interest_subgraph, k=2, iterations=50)
        
        # Color nodes by type
        node_colors = []
        for node in interest_subgraph.nodes():
            node_data = interest_subgraph.nodes[node]
            node_type = node_data.get('type', 'unknown')
            
            if node_type == 'user':
                node_colors.append('red')
            elif node_type == 'pin':
                node_colors.append('green')
            elif node_type == 'board':
                node_colors.append('orange')
            else:
                node_colors.append('gray')
        
        # Draw graph
        nx.draw_networkx_edges(
            interest_subgraph, pos,
            edge_color=self.config.edge_color,
            width=self.config.edge_width,
            alpha=0.6
        )
        
        nx.draw_networkx_nodes(
            interest_subgraph, pos,
            node_color=node_colors,
            node_size=self.config.node_size,
            alpha=0.8,
            edgecolors='black',
            linewidths=1
        )
        
        # Draw labels
        nx.draw_networkx_labels(
            interest_subgraph, pos,
            font_size=self.config.font_size,
            font_weight='bold'
        )
        
        # Create legend
        legend_elements = [
            patches.Patch(color='red', label='User'),
            patches.Patch(color='green', label='Pins'),
            patches.Patch(color='orange', label='Boards')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        plt.title(f"Interest Network for User: {user_id}", 
                 fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()

class DataStructureVisualizer:
    """Visualizer for data structures and algorithms"""
    
    def __init__(self, config: GraphLayoutConfig = None):
        self.config = config or GraphLayoutConfig()
    
    def visualize_trie_structure(self, trie, save_path: str = None, show: bool = True) -> None:
        """Visualize Trie structure"""
        plt.figure(figsize=self.config.figsize, dpi=self.config.dpi)
        
        # Create a networkx graph from trie
        G = nx.DiGraph()
        node_labels = {}
        node_colors = []
        
        def add_trie_nodes(node, node_id="root", depth=0):
            G.add_node(node_id)
            node_labels[node_id] = str(depth)
            
            # Color based on whether it's end of word
            if hasattr(node, 'is_end_of_word') and node.is_end_of_word:
                node_colors.append('red')
            else:
                node_colors.append('lightblue')
            
            child_id = 0
            for char, child_node in node.children.items():
                child_name = f"{node_id}_{char}_{child_id}"
                G.add_edge(node_id, child_name, label=char)
                add_trie_nodes(child_node, child_name, depth + 1)
                child_id += 1
        
        add_trie_nodes(trie.root)
        
        # Layout
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Draw edges with labels
        edge_labels = nx.get_edge_attributes(G, 'label')
        nx.draw_networkx_edges(G, pos, edge_color=self.config.edge_color, 
                              width=self.config.edge_width, alpha=0.6)
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, 
                                    font_size=self.config.font_size)
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                              node_size=self.config.node_size, alpha=0.8)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, labels=node_labels, 
                               font_size=self.config.font_size, font_weight='bold')
        
        plt.title("Trie Data Structure\n(Red = End of Word)", 
                 fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
    
    def visualize_priority_queue(self, priority_queue, save_path: str = None, show: bool = True) -> None:
        """Visualize priority queue as heap"""
        plt.figure(figsize=(10, 6), dpi=self.config.dpi)
        
        if not priority_queue.heap:
            plt.text(0.5, 0.5, "Empty Priority Queue", 
                    ha='center', va='center', fontsize=16)
            plt.title("Priority Queue (Empty)", fontsize=16, fontweight='bold')
            plt.axis('off')
            if show:
                plt.show()
            return
        
        # Extract items for visualization
        items = []
        for i, item in enumerate(priority_queue.heap):
            if hasattr(item, 'pin_id'):
                items.append((i, item.pin_id, item.score))
            else:
                items.append((i, str(item), getattr(item, 'score', 0)))
        
        # Create bar chart
        positions = [item[0] for item in items]
        labels = [item[1] for item in items]
        scores = [item[2] for item in items]
        
        bars = plt.bar(positions, scores, color='skyblue', edgecolor='navy', alpha=0.7)
        
        # Add value labels on bars
        for bar, score in zip(bars, scores):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{score:.2f}', ha='center', va='bottom', fontsize=self.config.font_size)
        
        plt.xlabel('Heap Position', fontsize=12)
        plt.ylabel('Priority Score', fontsize=12)
        plt.title('Priority Queue (Min-Heap Structure)\n(Higher values = Higher priority)', 
                 fontsize=16, fontweight='bold')
        
        # Set x-axis labels
        plt.xticks(positions, labels, rotation=45, ha='right')
        
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
    
    def visualize_hash_map_distribution(self, hash_map, save_path: str = None, show: bool = True) -> None:
        """Visualize hash map bucket distribution"""
        plt.figure(figsize=(12, 6), dpi=self.config.dpi)
        
        # Count items in each bucket
        bucket_counts = []
        for i, bucket in enumerate(hash_map.buckets):
            bucket_counts.append(len(bucket))
        
        # Create bar chart
        buckets = list(range(len(bucket_counts)))
        
        bars = plt.bar(buckets, bucket_counts, color='lightcoral', edgecolor='darkred', alpha=0.7)
        
        # Add value labels
        for bar, count in zip(bars, bucket_counts):
            if count > 0:
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        str(count), ha='center', va='bottom', fontsize=self.config.font_size)
        
        plt.xlabel('Bucket Index', fontsize=12)
        plt.ylabel('Number of Items', fontsize=12)
        plt.title(f'Hash Map Bucket Distribution\n(Capacity: {hash_map.capacity}, Size: {hash_map.size})', 
                 fontsize=16, fontweight='bold')
        
        # Add statistics
        if bucket_counts:
            max_bucket = max(bucket_counts)
            avg_bucket = sum(bucket_counts) / len(bucket_counts)
            empty_buckets = bucket_counts.count(0)
            
            stats_text = f'Max: {max_bucket}, Avg: {avg_bucket:.2f}, Empty: {empty_buckets}/{len(bucket_counts)}'
            plt.figtext(0.5, 0.02, stats_text, ha='center', fontsize=10, 
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()

class PerformanceVisualizer:
    """Visualizer for performance metrics and analytics"""
    
    def __init__(self, config: GraphLayoutConfig = None):
        self.config = config or GraphLayoutConfig()
    
    def visualize_algorithm_performance(self, performance_data: Dict[str, List], 
                                     save_path: str = None, show: bool = True) -> None:
        """Visualize algorithm performance comparison"""
        plt.figure(figsize=self.config.figsize, dpi=self.config.dpi)
        
        algorithms = list(performance_data.keys())
        metrics = list(performance_data[algorithms[0]].keys()) if algorithms else []
        
        # Create subplots for each metric
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        axes = axes.flatten()
        
        for i, metric in enumerate(metrics[:4]):  # Limit to 4 metrics
            ax = axes[i]
            
            values = [performance_data[alg][metric] for alg in algorithms]
            
            bars = ax.bar(algorithms, values, alpha=0.7)
            
            # Color bars differently
            colors = plt.cm.Set3(np.linspace(0, 1, len(algorithms)))
            for bar, color in zip(bars, colors):
                bar.set_color(color)
            
            ax.set_title(f'{metric.replace("_", " ").title()}', fontweight='bold')
            ax.set_ylabel('Value')
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                       f'{value:.3f}', ha='center', va='bottom', fontsize=9)
            
            ax.grid(axis='y', alpha=0.3)
        
        plt.suptitle('Algorithm Performance Comparison', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
    
    def visualize_feed_ranking_metrics(self, feed_data: List[Dict], 
                                    save_path: str = None, show: bool = True) -> None:
        """Visualize feed ranking metrics"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Extract metrics
        scores = [item.get('ranking_score', 0) for item in feed_data]
        engagement_factors = [item.get('relevance_factors', {}).get('engagement', 0) for item in feed_data]
        recency_factors = [item.get('relevance_factors', {}).get('recency', 0) for item in feed_data]
        affinity_factors = [item.get('relevance_factors', {}).get('user_affinity', 0) for item in feed_data]
        
        # 1. Score distribution
        ax1.hist(scores, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.set_title('Feed Score Distribution')
        ax1.set_xlabel('Score')
        ax1.set_ylabel('Frequency')
        ax1.grid(alpha=0.3)
        
        # 2. Relevance factors comparison
        factors_data = {
            'Engagement': engagement_factors,
            'Recency': recency_factors,
            'User Affinity': affinity_factors
        }
        
        for factor_name, factor_values in factors_data.items():
            ax2.plot(range(len(factor_values)), factor_values, label=factor_name, marker='o', markersize=3)
        
        ax2.set_title('Relevance Factors Over Feed Items')
        ax2.set_xlabel('Feed Position')
        ax2.set_ylabel('Factor Value')
        ax2.legend()
        ax2.grid(alpha=0.3)
        
        # 3. Factor correlation heatmap
        factor_matrix = np.array([engagement_factors, recency_factors, affinity_factors])
        factor_labels = ['Engagement', 'Recency', 'User Affinity']
        
        im = ax3.imshow(factor_matrix, cmap='YlOrRd', aspect='auto')
        ax3.set_xticks(range(len(feed_data)))
        ax3.set_yticks(range(len(factor_labels)))
        ax3.set_yticklabels(factor_labels)
        ax3.set_title('Relevance Factors Heatmap')
        
        plt.colorbar(im, ax=ax3, label='Factor Value')
        
        # 4. Score vs Factors scatter
        if len(scores) > 0:
            ax4.scatter(engagement_factors, scores, alpha=0.6, label='Engagement')
            ax4.scatter(recency_factors, scores, alpha=0.6, label='Recency')
            ax4.scatter(affinity_factors, scores, alpha=0.6, label='User Affinity')
            
        ax4.set_xlabel('Factor Value')
        ax4.set_ylabel('Feed Score')
        ax4.set_title('Score vs Relevance Factors')
        ax4.legend()
        ax4.grid(alpha=0.3)
        
        plt.suptitle('Feed Ranking Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
    
    def visualize_search_analytics(self, search_data: Dict, 
                                 save_path: str = None, show: bool = True) -> None:
        """Visualize search analytics and performance"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. Query response times
        response_times = search_data.get('response_times', [])
        if response_times:
            ax1.hist(response_times, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
            ax1.set_title('Query Response Times')
            ax1.set_xlabel('Response Time (ms)')
            ax1.set_ylabel('Frequency')
            ax1.grid(alpha=0.3)
        
        # 2. Suggestion types distribution
        suggestion_types = search_data.get('suggestion_types', {})
        if suggestion_types:
            types = list(suggestion_types.keys())
            counts = list(suggestion_types.values())
            
            ax2.pie(counts, labels=types, autopct='%1.1f%%', startangle=90)
            ax2.set_title('Suggestion Types Distribution')
        
        # 3. Popular queries
        popular_queries = search_data.get('popular_queries', {})
        if popular_queries:
            queries = list(popular_queries.keys())[:10]  # Top 10
            frequencies = list(popular_queries.values())[:10]
            
            ax3.barh(queries, frequencies, alpha=0.7, color='orange')
            ax3.set_title('Top 10 Popular Queries')
            ax3.set_xlabel('Frequency')
            ax3.invert_yaxis()
        
        # 4. Search performance over time
        performance_timeline = search_data.get('performance_timeline', {})
        if performance_timeline:
            timestamps = list(performance_timeline.keys())
            avg_times = list(performance_timeline.values())
            
            ax4.plot(timestamps, avg_times, marker='o', color='purple')
            ax4.set_title('Search Performance Over Time')
            ax4.set_xlabel('Time')
            ax4.set_ylabel('Average Response Time (ms)')
            ax4.grid(alpha=0.3)
        
        plt.suptitle('Search Analytics Dashboard', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.config.dpi, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()

class PinterestVisualizationSuite:
    """Complete visualization suite for Pinterest clone"""
    
    def __init__(self, output_dir: str = "visualizations"):
        self.output_dir = output_dir
        self.config = GraphLayoutConfig()
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize visualizers
        self.social_viz = SocialGraphVisualizer(self.config)
        self.interest_viz = InterestGraphVisualizer(self.config)
        self.ds_viz = DataStructureVisualizer(self.config)
        self.perf_viz = PerformanceVisualizer(self.config)
    
    def generate_all_visualizations(self, graph, cache_manager, search_index, 
                                  priority_manager, feed_ranker) -> Dict[str, str]:
        """Generate all visualizations and return file paths"""
        generated_files = {}
        
        # Social graph visualizations
        social_graph_path = os.path.join(self.output_dir, "social_graph.png")
        self.social_viz.visualize_social_graph(graph, social_graph_path, show=False)
        generated_files['social_graph'] = social_graph_path
        
        following_patterns_path = os.path.join(self.output_dir, "following_patterns.png")
        self.social_viz.visualize_following_patterns(graph, following_patterns_path, show=False)
        generated_files['following_patterns'] = following_patterns_path
        
        # Interest graph visualizations
        interest_graph_path = os.path.join(self.output_dir, "interest_graph.png")
        self.interest_viz.visualize_interest_graph(graph, interest_graph_path, show=False)
        generated_files['interest_graph'] = interest_graph_path
        
        # Data structure visualizations
        if hasattr(search_index, 'pin_content_trie'):
            trie_path = os.path.join(self.output_dir, "trie_structure.png")
            self.ds_viz.visualize_trie_structure(search_index.pin_content_trie, trie_path, show=False)
            generated_files['trie_structure'] = trie_path
        
        priority_queue_path = os.path.join(self.output_dir, "priority_queue.png")
        self.ds_viz.visualize_priority_queue(priority_manager.feed_queue, priority_queue_path, show=False)
        generated_files['priority_queue'] = priority_queue_path
        
        hash_map_path = os.path.join(self.output_dir, "hash_map_distribution.png")
        self.ds_viz.visualize_hash_map_distribution(cache_manager.pin_cache, hash_map_path, show=False)
        generated_files['hash_map_distribution'] = hash_map_path
        
        return generated_files
    
    def create_performance_dashboard(self, analytics_data: Dict, 
                                    save_path: str = None) -> str:
        """Create comprehensive performance dashboard"""
        dashboard_path = save_path or os.path.join(self.output_dir, "performance_dashboard.png")
        
        # Create a multi-panel dashboard
        fig = plt.figure(figsize=(20, 12))
        
        # This would be expanded with specific analytics visualizations
        # For now, create a placeholder
        plt.text(0.5, 0.5, "Performance Dashboard\n(Analytics data would be displayed here)", 
                ha='center', va='center', fontsize=20, 
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        plt.title("Pinterest Clone Performance Dashboard", fontsize=24, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        
        plt.savefig(dashboard_path, dpi=self.config.dpi, bbox_inches='tight')
        plt.close()
        
        return dashboard_path
