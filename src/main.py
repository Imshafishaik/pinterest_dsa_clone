#!/usr/bin/env python3

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from core_dsa.graph import PinterestGraph
from core_dsa.hash_map import PinterestCacheManager
from core_dsa.trie import PinterestSearchIndex
from core_dsa.priority_queue import PinterestPriorityManager
from features.feed_ranking import SmartFeedRanking
from features.search_autocomplete import SearchAutocomplete
from features.recommendation_engine import InterestGraphRecommender
from features.visual_search import VisualSearchEngine

app = Flask(__name__)
CORS(app)

graph = PinterestGraph()
cache_manager = PinterestCacheManager()
search_index = PinterestSearchIndex()
priority_manager = PinterestPriorityManager()
feed_ranker = SmartFeedRanking(graph, cache_manager)
autocomplete = SearchAutocomplete(search_index)
recommender = InterestGraphRecommender(graph, cache_manager)
visual_search = VisualSearchEngine()

def initialize_sample_data():
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
    
    # Add following relationships
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
    
    pins = [
        ("pin1", {"title": "DIY Wall Art Ideas", "description": "Creative DIY projects for home walls", "category": "craft", "likes": 245, "saves": 89, "author": "Alice"}),
        ("pin2", {"title": "Chocolate Chip Cookies", "description": "Best chocolate chip cookie recipe ever", "category": "food", "likes": 523, "saves": 201, "author": "Bob"}),
        ("pin3", {"title": "Sunset Photography Tips", "description": "How to take amazing travel photos", "category": "travel", "likes": 189, "saves": 67, "author": "Charlie"}),
        ("pin4", {"title": "Summer Fashion Trends", "description": "Hottest fashion trends for summer", "category": "fashion", "likes": 412, "saves": 156, "author": "Diana"}),
        ("pin5", {"title": "Morning Yoga Routine", "description": "Start your day with this yoga routine", "category": "fitness", "likes": 298, "saves": 112, "author": "Eve"}),
        ("pin6", {"title": "Best Gadgets 2024", "description": "Latest technology gadgets review", "category": "technology", "likes": 567, "saves": 234, "author": "Frank"}),
        ("pin7", {"title": "Watercolor Painting Tutorial", "description": "Learn watercolor painting step by step", "category": "art", "likes": 156, "saves": 78, "author": "Grace"}),
        ("pin8", {"title": "Guitar Chords for Beginners", "description": "Easy guitar chords to start with", "category": "music", "likes": 234, "saves": 98, "author": "Henry"}),
        ("pin9", {"title": "Upcycled Furniture Projects", "description": "Creative furniture upcycling ideas", "category": "craft", "likes": 198, "saves": 87, "author": "Alice"}),
        ("pin10", {"title": "Healthy Breakfast Ideas", "description": "Nutritious breakfast recipes", "category": "food", "likes": 345, "saves": 167, "author": "Bob"}),
        ("pin11", {"title": "Mountain Hiking Guide", "description": "Complete guide to mountain hiking", "category": "travel", "likes": 423, "saves": 189, "author": "Charlie"}),
        ("pin12", {"title": "Minimalist Wardrobe Essentials", "description": "Build a minimalist wardrobe", "category": "fashion", "likes": 289, "saves": 134, "author": "Diana"})
    ]
    
    for pin_id, pin_data in pins:
        graph.add_pin(pin_id, pin_data)
        pin_data['pin_id'] = pin_id
        pin_data['created_at'] = 1234567890
        pin_data['isLiked'] = False
        pin_data['isSaved'] = False
        pin_data['authorAvatar'] = f"https://picsum.photos/50/50?random={pin_id}"
        pin_data['imageUrl'] = f"https://picsum.photos/300/400?random={pin_id}"
        
        cache_manager.cache_pin(pin_id, pin_data)
        
        feed_ranker.update_feed_for_pin(pin_data)
        
        tags = [pin_data['category'], "ideas", "tutorial", "guide"]
        pin_data['tags'] = tags
        search_index.index_pin(pin_id, pin_data)
    
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
    
    for i in range(50):
        import random
        pin_id = random.choice([f"pin{i}" for i in range(1, 13)])
        priority_manager.record_pin_interaction(pin_id)

initialize_sample_data()

@app.route('/')
def home():
    return jsonify({
        'message': 'Pinterest Clone API',
        'version': '1.0.0',
        'features': [
            'Smart Feed Ranking',
            'Visual Search',
            'Interest Graph Traversal',
            'Search Autocomplete',
            'Consistent Hashing',
            'Trending Detection'
        ]
    })

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/api/pins', methods=['GET'])
def get_pins():
    pins = []
    for i in range(1, 13):
        pin_data = cache_manager.get_cached_pin(f"pin{i}")
        if pin_data:
            pins.append(pin_data)
    return jsonify(pins)

@app.route('/api/feed/<user_id>', methods=['GET'])
def get_feed(user_id):
    feed = feed_ranker.generate_user_feed(user_id, feed_size=10)
    return jsonify(feed)

@app.route('/api/search', methods=['GET'])
def search_pins():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    results = search_index.search_pins(query, k=20)
    return jsonify(results)

@app.route('/api/autocomplete', methods=['GET'])
def autocomplete_search():
    query = request.args.get('q', '')
    user_id = request.args.get('user_id', None)
    
    if not query:
        return jsonify([])
    
    suggestions = autocomplete.get_autocomplete_suggestions(query, user_id, k=10)
    return jsonify(suggestions)

@app.route('/api/recommendations/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    recommendations = recommender.recommend_pins(user_id, limit=10)
    
    recs = []
    for rec in recommendations:
        rec_data = {
            'pin_id': rec.item_id,
            'score': rec.score,
            'explanation': rec.explanation,
            'factors': rec.factors
        }
        pin_data = cache_manager.get_cached_pin(rec.item_id)
        if pin_data:
            rec_data.update(pin_data)
        recs.append(rec_data)
    
    return jsonify(recs)

@app.route('/api/trending', methods=['GET'])
def get_trending():
    trending = priority_manager.get_trending_content(limit=10)
    return jsonify(trending)

@app.route('/api/pin/<pin_id>/like', methods=['POST'])
def like_pin(pin_id):
    pin_data = cache_manager.get_cached_pin(pin_id)
    if pin_data:
        pin_data['likes'] = pin_data.get('likes', 0) + 1
        pin_data['isLiked'] = True
        cache_manager.cache_pin(pin_id, pin_data)
        return jsonify({'success': True, 'likes': pin_data['likes']})
    return jsonify({'error': 'Pin not found'}), 404

@app.route('/api/pin/<pin_id>/save', methods=['POST'])
def save_pin(pin_id):
    pin_data = cache_manager.get_cached_pin(pin_id)
    if pin_data:
        pin_data['saves'] = pin_data.get('saves', 0) + 1
        pin_data['isSaved'] = True
        cache_manager.cache_pin(pin_id, pin_data)
        return jsonify({'success': True, 'saves': pin_data['saves']})
    return jsonify({'error': 'Pin not found'}), 404

@app.route('/api/visual-search', methods=['POST'])
def visual_search():
    data = request.get_json()
    image_url = data.get('image_url', '')
    
    if not image_url:
        return jsonify({'error': 'Image URL required'}), 400
    
    for i in range(1, 7):
        visual_search.index_image(f"pin{i}", f"https://picsum.photos/300/400?random={i}")
    
    results = visual_search.search_similar_images(image_url, k=5)
    return jsonify(results)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = {
        'graph_stats': graph.get_graph_stats(),
        'cache_stats': cache_manager.get_stats(),
        'priority_stats': priority_manager.get_system_stats(),
        'search_stats': search_index.get_index_stats()
    }
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
