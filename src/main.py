#!/usr/bin/env python3

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
import hashlib
import uuid
import jwt
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from core_dsa.graph import PinterestGraph
from core_dsa.hash_map import PinterestCacheManager
from core_dsa.trie import PinterestSearchIndex
from core_dsa.priority_queue import PinterestPriorityManager
from core_dsa.queue import PinterestQueueManager
from features.feed_ranking import SmartFeedRanking
from features.search_autocomplete import SearchAutocomplete
from features.recommendation_engine import InterestGraphRecommender
from features.visual_search import VisualSearchEngine
from services.pin_service import PinService
from database.connection import db_manager
from database.models import Base, User

app = Flask(__name__)
CORS(app)

# Initialize database
db_manager.initialize()
Base.metadata.create_all(bind=db_manager.engine)

graph = PinterestGraph()
cache_manager = PinterestCacheManager()
search_index = PinterestSearchIndex()
priority_manager = PinterestPriorityManager()
queue_manager = PinterestQueueManager()
feed_ranker = SmartFeedRanking(graph, cache_manager)
autocomplete = SearchAutocomplete(search_index)
recommender = InterestGraphRecommender(graph, cache_manager)
visual_search = VisualSearchEngine()

# Create PinService after database is fully initialized
pin_service = PinService()

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
        
        # Add to database as well
        with db_manager.get_session() as session:
            existing_user = session.query(User).filter(
                (User.username == user_id) | (User.email == f"{user_id}@example.com")
            ).first()
            if not existing_user:
                password_hash = hashlib.sha256('password'.encode()).hexdigest()
                new_user = User(
                    username=user_id,
                    email=f"{user_id}@example.com",
                    password_hash=password_hash,
                    name=user_data.get('name', user_id)
                )
                session.add(new_user)
                session.commit()
    
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

@app.route('/api/pins', methods=['GET', 'POST'])
def pins():
    if request.method == 'GET':
        try:
            # Get pins from database using PinService
            db_pins = pin_service.get_all_pins(limit=50)
            
            # Also include any DSA-only pins (for backwards compatibility)
            dsa_pins = []
            for i in range(1, 13):
                pin_data = cache_manager.get_cached_pin(f"pin{i}")
                if pin_data and not any(p.get('id') == i for p in db_pins):
                    dsa_pins.append(pin_data)
            
            # Combine database pins with DSA pins
            all_pins = db_pins + dsa_pins
            return jsonify(all_pins)
            
        except Exception as e:
            # Fallback to DSA-only if database fails
            pins = []
            for i in range(1, 13):
                pin_data = cache_manager.get_cached_pin(f"pin{i}")
                if pin_data:
                    pins.append(pin_data)
            return jsonify(pins)
    
    elif request.method == 'POST':
        data = request.get_json()
        
        if not data or not data.get('title') or not data.get('image_url'):
            return jsonify({'error': 'Title and image_url are required'}), 400
        
        try:
            import time
            import random
            
            # Extract user from token
            user_id = 1
            author = 'Alice'
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if token:
                try:
                    payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
                    user_id = payload['user_id']
                    author = payload['name']
                except:
                    pass
            
            # Prepare data for database
            db_pin_data = {
                'title': data['title'],
                'description': data.get('description', ''),
                'image_url': data['image_url'],
                'link': data.get('link', ''),
                'creator_id': user_id,  # Use logged-in user
                'category': data.get('category', 'general'),
                'width': data.get('width', 300),
                'height': data.get('height', 400),
                'tag_names': data.get('tags', [])
            }
            
            # Save to database using PinService
            created_pin = pin_service.create_pin(db_pin_data)
            
            if not created_pin:
                return jsonify({'error': 'Failed to create pin'}), 500
            
            # Also add to DSA structures for performance
            pin_id = f"pin{created_pin['id']}"
            dsa_pin_data = {
                'pin_id': pin_id,
                'title': created_pin['title'],
                'description': created_pin['description'],
                'image_url': created_pin['image_url'],
                'link': created_pin.get('link', ''),
                'category': created_pin.get('category', 'general'),
                'author': author,
                'likes': 0,
                'saves': 0,
                'created_at': time.time(),
                'isLiked': False,
                'isSaved': False,
                'authorAvatar': data.get('author_avatar', f"https://picsum.photos/50/50?random={created_pin['id']}"),
                'tags': data.get('tags', [])
            }
            
            # Add to DSA structures
            graph.add_pin(pin_id, dsa_pin_data)
            cache_manager.cache_pin(pin_id, dsa_pin_data)
            feed_ranker.update_feed_for_pin(dsa_pin_data)
            
            tags = dsa_pin_data['tags'] + [dsa_pin_data['category'], "ideas", "tutorial"]
            dsa_pin_data['tags'] = tags
            search_index.index_pin(pin_id, dsa_pin_data)
            
            # Return the created pin with database info
            response_data = {
                **created_pin,
                'pin_id': pin_id,
                'isLiked': False,
                'isSaved': False,
                'authorAvatar': dsa_pin_data['authorAvatar']
            }
            
            return jsonify(response_data), 201
            
        except Exception as e:
            import traceback
            print(f"Error creating pin: {str(e)}")
            traceback.print_exc()
            return jsonify({'error': f'Database error: {str(e)}'}), 500

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
        
        # Track activity and notification
        user_id = request.headers.get('User-Id', 'anonymous')
        queue_manager.log_pin_activity(pin_id, user_id, 'save')
        queue_manager.add_notification(f"evt_{time.time()}", pin_data.get('author', 'Unknown'), 'save', {'pin_id': pin_id, 'user': user_id})
        
        return jsonify({'success': True, 'saves': pin_data['saves']})
    return jsonify({'error': 'Pin not found'}), 404

@app.route('/api/user/<user_id>/follow', methods=['POST'])
def follow_user(user_id):
    follower_id = 'alice' # Default fallback
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            follower_id = payload['username']
        except:
            pass
            
    # Assuming user_id parameter is the username of the user to follow
    graph.follow_user(follower_id, user_id)
    return jsonify({'success': True})

@app.route('/api/pin/<pin_id>/comment', methods=['POST'])
def comment_pin(pin_id):
    data = request.get_json()
    user_id = request.headers.get('User-Id', 'anonymous')
    comment = data.get('comment', '')
    if not comment:
        return jsonify({'error': 'Comment required'}), 400
        
    pin_data = cache_manager.get_cached_pin(pin_id)
    if pin_data:
        import time
        queue_manager.log_pin_activity(pin_id, user_id, 'comment', {'text': comment})
        queue_manager.add_notification(f"evt_{time.time()}", pin_data.get('author', 'Unknown'), 'comment', {'pin_id': pin_id, 'comment': comment, 'user': user_id})
        return jsonify({'success': True, 'message': 'Comment added'})
    return jsonify({'error': 'Pin not found'}), 404

@app.route('/api/notifications/<user_id>', methods=['GET'])
def get_notifications(user_id):
    # A mock route to fetch activities for a user representing their notifications.
    # Or, we could process notifications from the pipeline and return them.
    # In a real app, this would poll the pipeline or read a DB.
    # For now, let's process the batch and return any delivered ones, or just user activities.
    
    # Process some notifications in the background
    queue_manager.process_notifications(batch_size=10)
    
    # Return user's own activity as well for demonstration
    activities = queue_manager.get_user_activities(user_id)
    notifications = [{
        'id': f"act_{int(a.timestamp * 1000)}",
        'message': f"You performed '{a.action}' on pin {a.pin_id}",
        'timestamp': a.timestamp,
        'read': False
    } for a in activities]
    
    return jsonify(notifications)


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

JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')

def generate_jwt(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'name': user.name,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

# Authentication endpoints
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password') or not data.get('email'):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        with db_manager.get_session() as session:
            # Check if user already exists
            existing_user = session.query(User).filter(
                (User.username == data['username']) | (User.email == data['email'])
            ).first()
            
            if existing_user:
                return jsonify({'error': 'User already exists'}), 400
            
            # Create new user
            password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
            new_user = User(
                username=data['username'],
                email=data['email'],
                password_hash=password_hash,
                name=data.get('name', data['username'])
            )
            
            session.add(new_user)
            session.commit()
            
            # Create session JWT
            token = generate_jwt(new_user)
            
            return jsonify({
                'message': 'User registered successfully',
                'token': token,
                'user': {
                    'id': new_user.id,
                    'username': new_user.username,
                    'email': new_user.email,
                    'name': new_user.name
                }
            }), 201
            
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        with db_manager.get_session() as session:
            # Allow login with either username or email
            user = session.query(User).filter(
                (User.username == data['username']) | (User.email == data['username'])
            ).first()
            
            if not user:
                return jsonify({'error': 'Invalid credentials'}), 401
            
            # Verify password
            password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
            if user.password_hash != password_hash:
                return jsonify({'error': 'Invalid credentials'}), 401
            
            # Create session JWT
            token = generate_jwt(user)
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'name': user.name
                }
            }), 200
            
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    # Since JWTs are stateless, we can just tell the client to remove it.
    # In a full implementation, you might add the token to a blacklist cache.
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/auth/current', methods=['GET'])
def current_user():
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            return jsonify({
                'user': {
                    'id': payload['user_id'],
                    'username': payload['username'],
                    'email': payload['email'],
                    'name': payload['name']
                }
            }), 200
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
            
    except Exception as e:
        return jsonify({'error': f'Authentication failed: {str(e)}'}), 500

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
    app.run(debug=True, host='0.0.0.0', port=5001)
