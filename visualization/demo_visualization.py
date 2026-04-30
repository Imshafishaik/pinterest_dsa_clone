"""
Demo Visualization Script for Pinterest Clone
Creates sample visualizations to demonstrate the data structures and algorithms
"""

import sys
import os
import numpy as np
import time
import random

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core_dsa.graph import PinterestGraph
from core_dsa.hash_map import PinterestCacheManager
from core_dsa.trie import PinterestSearchIndex
from core_dsa.priority_queue import PinterestPriorityManager
from features.feed_ranking import SmartFeedRanking
from visualization.graph_visualizer import PinterestVisualizationSuite

def create_sample_data():
    """Create sample Pinterest data for visualization"""
    print("Creating sample Pinterest data...")
    
    # Create main components
    graph = PinterestGraph()
    cache_manager = PinterestCacheManager()
    search_index = PinterestSearchIndex()
    priority_manager = PinterestPriorityManager()
    feed_ranker = SmartFeedRanking(graph, cache_manager)
    
    # Create users
    users = [
        ("alice", {"name": "Alice", "interests": ["craft", "diy", "home"]}),
        ("bob", {"name": "Bob", "interests": ["food", "recipe", "cooking"]}),
        ("charlie", {"name": "Charlie", "interests": ["travel", "photography", "nature"]}),
        ("diana", {"name": "Diana", "interests": ["fashion", "style", "beauty"]}),
        ("eve", {"name": "Eve", "interests": ["fitness", "health", "wellness"]}),
        ("frank", {"name": "Frank", "interests": ["technology", "gadgets", "coding"]}),
        ("grace", {"name": "Grace", "interests": ["art", "painting", "design"]}),
        ("henry", {"name": "Henry", "interests": ["music", "guitar", "production"]})
    ]
    
    for user_id, user_data in users:
        graph.add_user(user_id, user_data)
    
    # Create following relationships
    following_pairs = [
        ("alice", "bob"), ("alice", "charlie"), ("alice", "diana"),
        ("bob", "alice"), ("bob", "eve"), ("bob", "frank"),
        ("charlie", "alice"), ("charlie", "grace"),
        ("diana", "alice"), ("diana", "grace"), ("diana", "henry"),
        ("eve", "bob"), ("eve", "frank"),
        ("frank", "bob"), ("frank", "henry"),
        ("grace", "charlie"), ("grace", "diana"),
        ("henry", "diana"), ("henry", "frank")
    ]
    
    for follower, following in following_pairs:
        graph.follow_user(follower, following)
    
    # Create pins
    pins = [
        ("pin1", {"title": "DIY Wall Art Ideas", "category": "craft", "likes": 25, "saves": 12, "comments": 3}),
        ("pin2", {"title": "Chocolate Chip Cookie Recipe", "category": "food", "likes": 45, "saves": 30, "comments": 8}),
        ("pin3", {"title": "Sunset Photography Tips", "category": "travel", "likes": 18, "saves": 8, "comments": 2}),
        ("pin4", {"title": "Summer Fashion Trends", "category": "fashion", "likes": 35, "saves": 20, "comments": 5}),
        ("pin5", {"title": "Morning Yoga Routine", "category": "fitness", "likes": 28, "saves": 15, "comments": 4}),
        ("pin6", {"title": "Best Gadgets 2024", "category": "technology", "likes": 52, "saves": 35, "comments": 12}),
        ("pin7", {"title": "Watercolor Painting Tutorial", "category": "art", "likes": 22, "saves": 10, "comments": 3}),
        ("pin8", {"title": "Guitar Chords for Beginners", "category": "music", "likes": 31, "saves": 18, "comments": 6}),
        ("pin9", {"title": "Upcycled Furniture Projects", "category": "craft", "likes": 19, "saves": 9, "comments": 2}),
        ("pin10", {"title": "Healthy Breakfast Ideas", "category": "food", "likes": 38, "saves": 25, "comments": 7}),
        ("pin11", {"title": "Mountain Hiking Guide", "category": "travel", "likes": 41, "saves": 28, "comments": 9}),
        ("pin12", {"title": "Minimalist Wardrobe Essentials", "category": "fashion", "likes": 29, "saves": 16, "comments": 4})
    ]
    
    for pin_id, pin_data in pins:
        graph.add_pin(pin_id, pin_data)
        pin_data['created_at'] = time.time() - random.randint(0, 86400 * 7)  # Random time in last week
        pin_data['pin_id'] = pin_id
        
        # Cache the pin
        cache_manager.cache_pin(pin_id, pin_data)
        
        # Add to feed ranking
        feed_ranker.update_feed_for_pin(pin_data)
        
        # Index for search
        tags = [pin_data['category'], "ideas", "tutorial", "guide"]
        pin_data['tags'] = tags
        search_index.index_pin(pin_id, pin_data)
    
    # Create boards
    boards = [
        ("board1", "DIY Projects", "craft"),
        ("board2", "Recipe Collection", "food"),
        ("board3", "Travel Inspiration", "travel"),
        ("board4", "Fashion Style", "fashion"),
        ("board5", "Fitness Goals", "fitness"),
        ("board6", "Tech Reviews", "technology"),
        ("board7", "Art Gallery", "art"),
        ("board8", "Music Lessons", "music")
    ]
    
    for board_id, board_name, category in boards:
        graph.add_board(board_id, {"name": board_name, "category": category})
        search_index.index_board(board_id, board_name)
    
    # Create pin-board-user relationships
    pin_assignments = [
        ("alice", "pin1", "board1"), ("alice", "pin9", "board1"),
        ("bob", "pin2", "board2"), ("bob", "pin10", "board2"),
        ("charlie", "pin3", "board3"), ("charlie", "pin11", "board3"),
        ("diana", "pin4", "board4"), ("diana", "pin12", "board4"),
        ("eve", "pin5", "board5"),
        ("frank", "pin6", "board6"),
        ("grace", "pin7", "board7"),
        ("henry", "pin8", "board8")
    ]
    
    for user_id, pin_id, board_id in pin_assignments:
        graph.save_pin_to_board(user_id, pin_id, board_id)
    
    # Add some interactions for trending detection
    for _ in range(50):
        pin_id = random.choice([f"pin{i}" for i in range(1, 13)])
        priority_manager.record_pin_interaction(pin_id)
    
    # Add some notifications
    notifications = [
        ("notif1", "alice", "new_follower", {"follower": "bob"}),
        ("notif2", "bob", "pin_saved", {"pin_id": "pin1", "user": "alice"}),
        ("notif3", "charlie", "board_updated", {"board_id": "board3"}),
        ("notif4", "diana", "new_follower", {"follower": "alice"}),
        ("notif5", "eve", "pin_saved", {"pin_id": "pin2", "user": "bob"})
    ]
    
    for notif_id, user_id, event_type, data in notifications:
        priority_manager.add_notification(notif_id, user_id, event_type, data)
    
    print("Sample data created successfully!")
    return graph, cache_manager, search_index, priority_manager, feed_ranker

def demonstrate_algorithms(graph, cache_manager, search_index, priority_manager, feed_ranker):
    """Demonstrate various algorithms and their performance"""
    print("\nDemonstrating Pinterest algorithms...")
    
    # 1. Feed Ranking
    print("\n1. Smart Feed Ranking:")
    start_time = time.time()
    feed = feed_ranker.generate_user_feed("alice", feed_size=5)
    feed_time = time.time() - start_time
    
    print(f"   Generated feed for Alice in {feed_time:.4f} seconds")
    print(f"   Feed contains {len(feed)} pins")
    for i, item in enumerate(feed[:3]):
        print(f"   {i+1}. {item['pin_data']['title']} (Score: {item['ranking_score']:.3f})")
    
    # 2. Search Autocomplete
    print("\n2. Search Autocomplete:")
    from features.search_autocomplete import SearchAutocomplete
    autocomplete = SearchAutocomplete(search_index)
    
    start_time = time.time()
    suggestions = autocomplete.get_autocomplete_suggestions("craft", user_id="alice")
    search_time = time.time() - start_time
    
    print(f"   Found {len(suggestions['suggestions'])} suggestions for 'craft' in {search_time:.4f} seconds")
    for i, suggestion in enumerate(suggestions['suggestions'][:3]):
        print(f"   {i+1}. {suggestion['text']} (Score: {suggestion['relevance_score']:.3f})")
    
    # 3. Recommendations
    print("\n3. Interest Graph Recommendations:")
    from features.recommendation_engine import InterestGraphRecommender
    recommender = InterestGraphRecommender(graph, cache_manager)
    
    start_time = time.time()
    recommendations = recommender.recommend_pins("alice", limit=3)
    rec_time = time.time() - start_time
    
    print(f"   Generated {len(recommendations)} recommendations for Alice in {rec_time:.4f} seconds")
    for i, rec in enumerate(recommendations):
        print(f"   {i+1}. Pin {rec.item_id} (Score: {rec.score:.3f}) - {rec.explanation}")
    
    # 4. Trending Detection
    print("\n4. Trending Content:")
    start_time = time.time()
    trending = priority_manager.get_trending_content(limit=3)
    trending_time = time.time() - start_time
    
    print(f"   Found {len(trending)} trending pins in {trending_time:.4f} seconds")
    for i, pin in enumerate(trending):
        print(f"   {i+1}. Pin {pin['pin_id']} (Velocity: {pin['velocity']:.2f})")
    
    # 5. Visual Search (Mock)
    print("\n5. Visual Search:")
    from features.visual_search import VisualSearchEngine
    visual_search = VisualSearchEngine(embedding_dim=32)
    
    # Index some images
    for i in range(1, 7):
        visual_search.index_image(f"pin{i}", f"http://example.com/image{i}.jpg")
    
    start_time = time.time()
    search_results = visual_search.search_similar_images("http://example.com/image1.jpg", k=3)
    visual_time = time.time() - start_time
    
    print(f"   Visual search completed in {visual_time:.4f} seconds")
    print(f"   Found {len(search_results['results'])} similar images")
    
    # 6. Graph Traversal
    print("\n6. Graph Traversal Algorithms:")
    
    # BFS for similar pins
    start_time = time.time()
    similar_pins = graph.bfs_find_similar_pins("pin1", max_depth=2)
    bfs_time = time.time() - start_time
    
    print(f"   BFS found {len(similar_pins)} similar pins to pin1 in {bfs_time:.4f} seconds")
    
    # DFS for user interests
    start_time = time.time()
    interests = graph.dfs_explore_interests("alice", max_depth=2)
    dfs_time = time.time() - start_time
    
    print(f"   DFS explored Alice's interests in {dfs_time:.4f} seconds")
    print(f"   Found {len(interests['pins'])} pins, {len(interests['boards'])} boards")
    
    # 7. PageRank Authority
    print("\n7. PageRank Authority Calculation:")
    start_time = time.time()
    authority_scores = graph.calculate_pin_authority()
    pagerank_time = time.time() - start_time
    
    print(f"   Calculated authority scores for {len(authority_scores)} pins in {pagerank_time:.4f} seconds")
    
    # Show top authority pins
    top_pins = sorted(authority_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    for i, (pin_id, score) in enumerate(top_pins):
        print(f"   {i+1}. Pin {pin_id} (Authority: {score:.4f})")

def create_visualization_demo():
    """Create comprehensive visualization demo"""
    print("Creating Pinterest Clone Visualization Demo")
    print("=" * 50)
    
    # Create sample data
    graph, cache_manager, search_index, priority_manager, feed_ranker = create_sample_data()
    
    # Demonstrate algorithms
    demonstrate_algorithms(graph, cache_manager, search_index, priority_manager, feed_ranker)
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    
    viz_suite = PinterestVisualizationSuite(output_dir="demo_visualizations")
    generated_files = viz_suite.generate_all_visualizations(
        graph, cache_manager, search_index, priority_manager, feed_ranker
    )
    
    print(f"\nGenerated {len(generated_files)} visualization files:")
    for name, path in generated_files.items():
        print(f"  - {name}: {path}")
    
    # Create performance dashboard
    dashboard_path = viz_suite.create_performance_dashboard({})
    print(f"  - performance_dashboard: {dashboard_path}")
    
    print("\n" + "=" * 50)
    print("Demo completed successfully!")
    print("Check the 'demo_visualizations' folder for generated images.")
    
    return generated_files

if __name__ == "__main__":
    # Set random seed for reproducible results
    random.seed(42)
    np.random.seed(42)
    
    # Run the demo
    create_visualization_demo()
