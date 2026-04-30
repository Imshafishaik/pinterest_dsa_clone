#!/usr/bin/env python3
"""
Production-Ready Pinterest Clone Application
With PostgreSQL database, Redis caching, and proper architecture
"""

import os
import sys
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from database.connection import db_manager, get_config
from database.migrations import run_migrations, reset_database
from services.pin_service import pin_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Get configuration
config = get_config()
app.config.from_object(config)

# Enable CORS
CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

# Initialize database
try:
    db_manager.initialize()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    sys.exit(1)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

# Health check endpoint
@app.route('/health')
def health_check():
    """Comprehensive health check"""
    try:
        health = db_manager.health_check()
        health['timestamp'] = datetime.now().isoformat()
        health['version'] = '2.0.0'
        health['environment'] = os.getenv('FLASK_ENV', 'development')
        
        status_code = 200 if all(health[k] for k in ['database', 'redis']) else 503
        return jsonify(health), status_code
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'error': 'Health check failed'}), 500

# API Routes
@app.route('/')
def home():
    return jsonify({
        'message': 'Pinterest Clone API - Production Ready',
        'version': '2.0.0',
        'features': [
            'PostgreSQL Database',
            'Redis Caching',
            'Smart Feed Ranking (O(n log k))',
            'Visual Search (K-d Tree)',
            'Interest Graph Traversal',
            'Search Autocomplete (Trie)',
            'Trending Detection',
            'User Authentication',
            'Pin Management'
        ],
        'endpoints': {
            'pins': '/api/pins',
            'feed': '/api/feed/{user_id}',
            'search': '/api/search?q={query}',
            'trending': '/api/trending',
            'categories': '/api/categories',
            'health': '/health'
        }
    })

# Pin endpoints
@app.route('/api/pins', methods=['GET'])
def get_pins():
    """Get all pins with pagination"""
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        category = request.args.get('category')
        
        if category:
            pins = pin_service.get_pins_by_category(category, limit, offset)
        else:
            pins = pin_service.get_all_pins(limit, offset)
        
        return jsonify({
            'pins': pins,
            'limit': limit,
            'offset': offset,
            'total': len(pins)
        })
    except Exception as e:
        logger.error(f"Error getting pins: {e}")
        return jsonify({'error': 'Failed to get pins'}), 500

@app.route('/api/pins/<int:pin_id>', methods=['GET'])
def get_pin(pin_id):
    """Get specific pin by ID"""
    try:
        pin = pin_service.get_pin_by_id(pin_id)
        if not pin:
            return jsonify({'error': 'Pin not found'}), 404
        return jsonify(pin)
    except Exception as e:
        logger.error(f"Error getting pin {pin_id}: {e}")
        return jsonify({'error': 'Failed to get pin'}), 500

@app.route('/api/pins', methods=['POST'])
def create_pin():
    """Create a new pin"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'image_url', 'creator_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        pin = pin_service.create_pin(data)
        if not pin:
            return jsonify({'error': 'Failed to create pin'}), 500
        
        return jsonify(pin), 201
    except Exception as e:
        logger.error(f"Error creating pin: {e}")
        return jsonify({'error': 'Failed to create pin'}), 500

@app.route('/api/pins/<int:pin_id>', methods=['PUT'])
def update_pin(pin_id):
    """Update a pin"""
    try:
        data = request.get_json()
        pin = pin_service.update_pin(pin_id, data)
        if not pin:
            return jsonify({'error': 'Pin not found or update failed'}), 404
        return jsonify(pin)
    except Exception as e:
        logger.error(f"Error updating pin {pin_id}: {e}")
        return jsonify({'error': 'Failed to update pin'}), 500

@app.route('/api/pins/<int:pin_id>', methods=['DELETE'])
def delete_pin(pin_id):
    """Delete a pin"""
    try:
        user_id = request.json.get('user_id') if request.is_json else None
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        success = pin_service.delete_pin(pin_id, user_id)
        if not success:
            return jsonify({'error': 'Pin not found or unauthorized'}), 404
        
        return jsonify({'message': 'Pin deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting pin {pin_id}: {e}")
        return jsonify({'error': 'Failed to delete pin'}), 500

# Interaction endpoints
@app.route('/api/pins/<int:pin_id>/like', methods=['POST'])
def like_pin(pin_id):
    """Like a pin"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        success = pin_service.like_pin(pin_id, user_id)
        if not success:
            return jsonify({'error': 'Already liked or failed'}), 400
        
        # Record interaction
        pin_service.record_interaction(pin_id, user_id, 'like')
        
        return jsonify({'message': 'Pin liked successfully'})
    except Exception as e:
        logger.error(f"Error liking pin {pin_id}: {e}")
        return jsonify({'error': 'Failed to like pin'}), 500

@app.route('/api/pins/<int:pin_id>/unlike', methods=['POST'])
def unlike_pin(pin_id):
    """Unlike a pin"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        success = pin_service.unlike_pin(pin_id, user_id)
        if not success:
            return jsonify({'error': 'Not liked or failed'}), 400
        
        return jsonify({'message': 'Pin unliked successfully'})
    except Exception as e:
        logger.error(f"Error unliking pin {pin_id}: {e}")
        return jsonify({'error': 'Failed to unlike pin'}), 500

@app.route('/api/pins/<int:pin_id>/save', methods=['POST'])
def save_pin(pin_id):
    """Save a pin"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        board_id = data.get('board_id')
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        success = pin_service.save_pin(pin_id, user_id, board_id)
        if not success:
            return jsonify({'error': 'Already saved or failed'}), 400
        
        # Record interaction
        pin_service.record_interaction(pin_id, user_id, 'save')
        
        return jsonify({'message': 'Pin saved successfully'})
    except Exception as e:
        logger.error(f"Error saving pin {pin_id}: {e}")
        return jsonify({'error': 'Failed to save pin'}), 500

@app.route('/api/pins/<int:pin_id>/unsave', methods=['POST'])
def unsave_pin(pin_id):
    """Unsave a pin"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        success = pin_service.unsave_pin(pin_id, user_id)
        if not success:
            return jsonify({'error': 'Not saved or failed'}), 400
        
        return jsonify({'message': 'Pin unsaved successfully'})
    except Exception as e:
        logger.error(f"Error unsaving pin {pin_id}: {e}")
        return jsonify({'error': 'Failed to unsave pin'}), 500

# Search endpoints
@app.route('/api/search', methods=['GET'])
def search_pins():
    """Search pins"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Search query required'}), 400
        
        limit = min(int(request.args.get('limit', 20)), 50)
        category = request.args.get('category')
        
        results = pin_service.search_pins(query, limit, category)
        
        # Record search interaction (mock user for now)
        pin_service.record_interaction(1, 1, 'search', {'query': query, 'category': category})
        
        return jsonify({
            'query': query,
            'results': results,
            'total': len(results)
        })
    except Exception as e:
        logger.error(f"Error searching pins: {e}")
        return jsonify({'error': 'Failed to search pins'}), 500

# Trending endpoints
@app.route('/api/trending', methods=['GET'])
def get_trending():
    """Get trending pins"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)
        time_window = int(request.args.get('time_window_hours', 24))
        
        trending = pin_service.get_trending_pins(limit, time_window)
        
        return jsonify({
            'trending': trending,
            'time_window_hours': time_window,
            'total': len(trending)
        })
    except Exception as e:
        logger.error(f"Error getting trending pins: {e}")
        return jsonify({'error': 'Failed to get trending pins'}), 500

# Category endpoints
@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get available categories"""
    try:
        with db_manager.get_session() as session:
            from database.models import Pin
            
            categories = session.query(Pin.category)\
                              .filter(Pin.category.isnot(None))\
                              .distinct()\
                              .all()
            
            category_list = [cat[0] for cat in categories]
            return jsonify({'categories': sorted(category_list)})
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({'error': 'Failed to get categories'}), 500

@app.route('/api/categories/<category>/pins', methods=['GET'])
def get_category_pins(category):
    """Get pins by category"""
    try:
        limit = min(int(request.args.get('limit', 20)), 50)
        offset = int(request.args.get('offset', 0))
        
        pins = pin_service.get_pins_by_category(category, limit, offset)
        
        return jsonify({
            'category': category,
            'pins': pins,
            'limit': limit,
            'offset': offset,
            'total': len(pins)
        })
    except Exception as e:
        logger.error(f"Error getting category pins: {e}")
        return jsonify({'error': 'Failed to get category pins'}), 500

# Stats endpoints
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        with db_manager.get_session() as session:
            from database.models import Pin, User, Like, Save, Interaction
            
            stats = {
                'pins': session.query(Pin).filter(Pin.is_active == True).count(),
                'users': session.query(User).filter(User.is_active == True).count(),
                'likes': session.query(Like).count(),
                'saves': session.query(Save).count(),
                'interactions': session.query(Interaction).count(),
                'cache_health': db_manager.health_check(),
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Failed to get stats'}), 500

# Database management endpoints (development only)
@app.route('/api/admin/migrate', methods=['POST'])
def run_migrations_endpoint():
    """Run database migrations (development only)"""
    if os.getenv('FLASK_ENV') == 'production':
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        run_migrations()
        return jsonify({'message': 'Migrations completed successfully'})
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return jsonify({'error': 'Migration failed'}), 500

@app.route('/api/admin/reset', methods=['POST'])
def reset_database_endpoint():
    """Reset database (development only)"""
    if os.getenv('FLASK_ENV') == 'production':
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        reset_database()
        return jsonify({'message': 'Database reset successfully'})
    except Exception as e:
        logger.error(f"Database reset error: {e}")
        return jsonify({'error': 'Database reset failed'}), 500

# Request logging
@app.before_request
def before_request():
    """Log request information"""
    g.start_time = datetime.now()
    
@app.after_request
def after_request(response):
    """Log response information"""
    if hasattr(g, 'start_time'):
        duration = (datetime.now() - g.start_time).total_seconds()
        logger.info(f"{request.method} {request.path} - {response.status_code} - {duration:.3f}s")
    return response

if __name__ == '__main__':
    # Check if database is set up
    health = db_manager.health_check()
    if not all(health[k] for k in ['database', 'redis']):
        logger.error("Database or Redis not available. Please check your configuration.")
        sys.exit(1)
    
    # Run migrations if needed
    if os.getenv('RUN_MIGRATIONS', 'true').lower() == 'true':
        try:
            logger.info("Running database migrations...")
            run_migrations()
            logger.info("Migrations completed successfully")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
    
    # Start the application
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Pinterest Clone API on port {port}")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
