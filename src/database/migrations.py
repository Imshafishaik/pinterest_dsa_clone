

from sqlalchemy.orm import Session
from sqlalchemy import text
from .models import User, Pin, Board, Tag, Like, Save, Comment, Interaction
from .connection import db_manager, cache_manager
import hashlib
import random
from datetime import datetime, timedelta

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_sample_users(session: Session):
    users_data = [
        {
            'username': 'alice_creative',
            'email': 'alice@example.com',
            'password': 'password123',
            'name': 'Alice Johnson',
            'bio': 'DIY enthusiast | Home decor lover | Finding inspiration in everyday things 🎨✨',
            'avatar_url': 'https://picsum.photos/200/200?random=alice'
        },
        {
            'username': 'bob_foodie',
            'email': 'bob@example.com',
            'password': 'password123',
            'name': 'Bob Smith',
            'bio': 'Chef | Recipe developer | Food photographer 🍳📸',
            'avatar_url': 'https://picsum.photos/200/200?random=bob'
        },
        {
            'username': 'charlie_travel',
            'email': 'charlie@example.com',
            'password': 'password123',
            'name': 'Charlie Brown',
            'bio': 'Travel blogger | Adventure seeker | Photography enthusiast ✈️🌍',
            'avatar_url': 'https://picsum.photos/200/200?random=charlie'
        },
        {
            'username': 'diana_style',
            'email': 'diana@example.com',
            'password': 'password123',
            'name': 'Diana Prince',
            'bio': 'Fashion designer | Style consultant | Trendsetter 👗👠',
            'avatar_url': 'https://picsum.photos/200/200?random=diana'
        },
        {
            'username': 'eve_fitness',
            'email': 'eve@example.com',
            'password': 'password123',
            'name': 'Eve Wilson',
            'bio': 'Personal trainer | Yoga instructor | Wellness coach 💪🧘‍♀️',
            'avatar_url': 'https://picsum.photos/200/200?random=eve'
        },
        {
            'username': 'frank_tech',
            'email': 'frank@example.com',
            'password': 'password123',
            'name': 'Frank Miller',
            'bio': 'Tech enthusiast | Gadget reviewer | Coding wizard 💻🔧',
            'avatar_url': 'https://picsum.photos/200/200?random=frank'
        },
        {
            'username': 'grace_artist',
            'email': 'grace@example.com',
            'password': 'password123',
            'name': 'Grace Lee',
            'bio': 'Artist | Painter | Creative soul 🎨🖌️',
            'avatar_url': 'https://picsum.photos/200/200?random=grace'
        },
        {
            'username': 'henry_music',
            'email': 'henry@example.com',
            'password': 'password123',
            'name': 'Henry Davis',
            'bio': 'Musician | Guitarist | Producer 🎸🎵',
            'avatar_url': 'https://picsum.photos/200/200?random=henry'
        }
    ]
    
    created_users = []
    for user_data in users_data:
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            password_hash=hash_password(user_data['password']),
            name=user_data['name'],
            bio=user_data['bio'],
            avatar_url=user_data['avatar_url'],
            is_verified=True
        )
        session.add(user)
        created_users.append(user)
    
    session.commit()
    return created_users

def create_sample_tags(session: Session):
    tags_data = [
        {'name': 'diy', 'category': 'craft'},
        {'name': 'craft', 'category': 'craft'},
        {'name': 'home-decor', 'category': 'home'},
        {'name': 'recipe', 'category': 'food'},
        {'name': 'cooking', 'category': 'food'},
        {'name': 'baking', 'category': 'food'},
        {'name': 'travel', 'category': 'travel'},
        {'name': 'photography', 'category': 'travel'},
        {'name': 'fashion', 'category': 'fashion'},
        {'name': 'style', 'category': 'fashion'},
        {'name': 'fitness', 'category': 'fitness'},
        {'name': 'yoga', 'category': 'fitness'},
        {'name': 'technology', 'category': 'tech'},
        {'name': 'gadgets', 'category': 'tech'},
        {'name': 'art', 'category': 'art'},
        {'name': 'painting', 'category': 'art'},
        {'name': 'music', 'category': 'music'},
        {'name': 'guitar', 'category': 'music'},
        {'name': 'ideas', 'category': 'general'},
        {'name': 'tutorial', 'category': 'general'},
        {'name': 'guide', 'category': 'general'},
        {'name': 'creative', 'category': 'general'},
        {'name': 'inspiration', 'category': 'general'}
    ]
    
    created_tags = []
    for tag_data in tags_data:
        tag = Tag(name=tag_data['name'], category=tag_data['category'])
        session.add(tag)
        created_tags.append(tag)
    
    session.commit()
    return created_tags

def create_sample_boards(session: Session, users):
    boards_data = [
        {'name': 'DIY Projects', 'category': 'craft', 'creator_id': users[0].id},
        {'name': 'Recipe Collection', 'category': 'food', 'creator_id': users[1].id},
        {'name': 'Travel Inspiration', 'category': 'travel', 'creator_id': users[2].id},
        {'name': 'Fashion Style', 'category': 'fashion', 'creator_id': users[3].id},
        {'name': 'Fitness Goals', 'category': 'fitness', 'creator_id': users[4].id},
        {'name': 'Tech Reviews', 'category': 'tech', 'creator_id': users[5].id},
        {'name': 'Art Gallery', 'category': 'art', 'creator_id': users[6].id},
        {'name': 'Music Lessons', 'category': 'music', 'creator_id': users[7].id},
        {'name': 'Home Decor Ideas', 'category': 'home', 'creator_id': users[0].id},
        {'name': 'Baking Adventures', 'category': 'food', 'creator_id': users[1].id},
        {'name': 'Photography Tips', 'category': 'travel', 'creator_id': users[2].id},
        {'name': 'Minimalist Style', 'category': 'fashion', 'creator_id': users[3].id}
    ]
    
    created_boards = []
    for board_data in boards_data:
        board = Board(
            name=board_data['name'],
            category=board_data['category'],
            creator_id=board_data['creator_id'],
            description=f"Collection of {board_data['name']} ideas and inspiration"
        )
        session.add(board)
        created_boards.append(board)
    
    session.commit()
    return created_boards

def create_sample_pins(session: Session, users, boards, tags):
    pins_data = [
        {
            'title': 'DIY Wall Art Ideas',
            'description': 'Creative DIY projects for home walls using recycled materials',
            'image_url': 'https://picsum.photos/400/500?random=1',
            'creator_id': users[0].id,
            'category': 'craft',
            'width': 400,
            'height': 500,
            'tag_names': ['diy', 'craft', 'home-decor', 'creative', 'ideas']
        },
        {
            'title': 'Chocolate Chip Cookies Recipe',
            'description': 'Best chocolate chip cookie recipe ever - crispy edges, chewy center',
            'image_url': 'https://picsum.photos/400/450?random=2',
            'creator_id': users[1].id,
            'category': 'food',
            'width': 400,
            'height': 450,
            'tag_names': ['recipe', 'cooking', 'baking', 'tutorial']
        },
        {
            'title': 'Sunset Photography Tips',
            'description': 'How to take amazing travel photos during golden hour',
            'image_url': 'https://picsum.photos/400/350?random=3',
            'creator_id': users[2].id,
            'category': 'travel',
            'width': 400,
            'height': 350,
            'tag_names': ['travel', 'photography', 'tips', 'guide']
        },
        {
            'title': 'Summer Fashion Trends 2024',
            'description': 'Hottest fashion trends for summer - what to wear and how to style',
            'image_url': 'https://picsum.photos/400/550?random=4',
            'creator_id': users[3].id,
            'category': 'fashion',
            'width': 400,
            'height': 550,
            'tag_names': ['fashion', 'style', 'trends', 'guide']
        },
        {
            'title': 'Morning Yoga Routine',
            'description': 'Start your day with this energizing 15-minute yoga routine',
            'image_url': 'https://picsum.photos/400/380?random=5',
            'creator_id': users[4].id,
            'category': 'fitness',
            'width': 400,
            'height': 380,
            'tag_names': ['fitness', 'yoga', 'routine', 'tutorial']
        },
        {
            'title': 'Best Tech Gadgets 2024',
            'description': 'Latest technology gadgets review - must-have devices this year',
            'image_url': 'https://picsum.photos/400/420?random=6',
            'creator_id': users[5].id,
            'category': 'tech',
            'width': 400,
            'height': 420,
            'tag_names': ['technology', 'gadgets', 'review', 'guide']
        },
        {
            'title': 'Watercolor Painting Tutorial',
            'description': 'Learn watercolor painting step by step - beginner friendly guide',
            'image_url': 'https://picsum.photos/400/360?random=7',
            'creator_id': users[6].id,
            'category': 'art',
            'width': 400,
            'height': 360,
            'tag_names': ['art', 'painting', 'tutorial', 'creative']
        },
        {
            'title': 'Guitar Chords for Beginners',
            'description': 'Easy guitar chords to start with - complete beginner guide',
            'image_url': 'https://picsum.photos/400/440?random=8',
            'creator_id': users[7].id,
            'category': 'music',
            'width': 400,
            'height': 440,
            'tag_names': ['music', 'guitar', 'tutorial', 'guide']
        },
        {
            'title': 'Upcycled Furniture Projects',
            'description': 'Creative furniture upcycling ideas - transform old pieces into treasures',
            'image_url': 'https://picsum.photos/400/480?random=9',
            'creator_id': users[0].id,
            'category': 'craft',
            'width': 400,
            'height': 480,
            'tag_names': ['diy', 'craft', 'home-decor', 'creative', 'ideas']
        },
        {
            'title': 'Healthy Breakfast Ideas',
            'description': 'Nutritious breakfast recipes to start your day right',
            'image_url': 'https://picsum.photos/400/460?random=10',
            'creator_id': users[1].id,
            'category': 'food',
            'width': 400,
            'height': 460,
            'tag_names': ['recipe', 'cooking', 'healthy', 'ideas']
        },
        {
            'title': 'Mountain Hiking Guide',
            'description': 'Complete guide to mountain hiking - safety tips and best trails',
            'image_url': 'https://picsum.photos/400/490?random=11',
            'creator_id': users[2].id,
            'category': 'travel',
            'width': 400,
            'height': 490,
            'tag_names': ['travel', 'hiking', 'guide', 'tips']
        },
        {
            'title': 'Minimalist Wardrobe Essentials',
            'description': 'Build a minimalist wardrobe with these essential pieces',
            'image_url': 'https://picsum.photos/400/470?random=12',
            'creator_id': users[3].id,
            'category': 'fashion',
            'width': 400,
            'height': 470,
            'tag_names': ['fashion', 'style', 'minimalist', 'guide']
        }
    ]
    
    tag_map = {tag.name: tag for tag in tags}
    
    created_pins = []
    for pin_data in pins_data:
        pin = Pin(
            title=pin_data['title'],
            description=pin_data['description'],
            image_url=pin_data['image_url'],
            creator_id=pin_data['creator_id'],
            category=pin_data['category'],
            width=pin_data['width'],
            height=pin_data['height']
        )
        session.add(pin)
        session.flush()  
        created_pins.append(pin)
        
        for tag_name in pin_data['tag_names']:
            if tag_name in tag_map:
                pin.tags.append(tag_map[tag_name])
    
    session.commit()
    return created_pins

def create_sample_interactions(session: Session, users, pins):
    """Create sample interactions for trending detection"""
    interaction_types = ['view', 'click', 'share']
    
    base_time = datetime.now() - timedelta(days=7)
    
    for i in range(500): 
        user = random.choice(users)
        pin = random.choice(pins)
        interaction_type = random.choice(interaction_types)
        
        random_hours = random.randint(0, 24 * 7)
        interaction_time = base_time + timedelta(hours=random_hours)
        
        interaction = Interaction(
            user_id=user.id,
            pin_id=pin.id,
            interaction_type=interaction_type,
            created_at=interaction_time
        )
        session.add(interaction)
    
    session.commit()

def create_sample_likes_saves(session: Session, users, pins):
    # Create likes
    for i in range(200):
        user = random.choice(users)
        pin = random.choice(pins)
        
        # Check if like already exists
        existing = session.query(Like).filter(
            Like.user_id == user.id,
            Like.pin_id == pin.id
        ).first()
        
        if not existing:
            like = Like(user_id=user.id, pin_id=pin.id)
            session.add(like)
    
    # Create saves
    for i in range(150):
        user = random.choice(users)
        pin = random.choice(pins)
        
        # Check if save already exists
        existing = session.query(Save).filter(
            Save.user_id == user.id,
            Save.pin_id == pin.id
        ).first()
        
        if not existing:
            save = Save(user_id=user.id, pin_id=pin.id)
            session.add(save)
    
    session.commit()

def create_following_relationships(session: Session, users):
    following_pairs = [
        (users[0], users[1]), (users[0], users[2]), (users[0], users[3]),
        (users[1], users[0]), (users[1], users[4]), (users[1], users[5]),
        (users[2], users[0]), (users[2], users[6]),
        (users[3], users[0]), (users[3], users[6]), (users[3], users[7]),
        (users[4], users[1]), (users[4], users[5]),
        (users[5], users[1]), (users[5], users[7]),
        (users[6], users[2]), (users[6], users[3]),
        (users[7], users[3]), (users[7], users[5])
    ]
    
    for follower, following in following_pairs:
        # Check if relationship already exists
        existing = session.query(users[0].__class__).filter(
            user_followers.c.follower_id == follower.id,
            user_followers.c.following_id == following.id
        ).first()
        
        if not existing:
            follower.following.append(following)
    
    session.commit()

def pin_board_assignments(session: Session, pins, boards, users):
    """Assign pins to boards"""
    assignments = [
        (pins[0], boards[0]), (pins[8], boards[0]),  # DIY pins to DIY Projects
        (pins[1], boards[1]), (pins[9], boards[1]),  # Food pins to Recipe Collection
        (pins[2], boards[2]), (pins[10], boards[2]), # Travel pins to Travel Inspiration
        (pins[3], boards[3]), (pins[11], boards[3]), # Fashion pins to Fashion Style
        (pins[4], boards[4]),  # Fitness pin to Fitness Goals
        (pins[5], boards[5]),  # Tech pin to Tech Reviews
        (pins[6], boards[6]),  # Art pin to Art Gallery
        (pins[7], boards[7]),  # Music pin to Music Lessons
        (pins[0], boards[8]),  # DIY pin to Home Decor Ideas
        (pins[1], boards[9]),  # Food pin to Baking Adventures
        (pins[2], boards[10]), # Travel pin to Photography Tips
        (pins[3], boards[11])  # Fashion pin to Minimalist Style
    ]
    
    for pin, board in assignments:
        pin.boards.append(board)
    
    session.commit()

def run_migrations():
    """Run all database migrations"""
    try:
        with db_manager.get_session() as session:
            print("Creating sample users...")
            users = create_sample_users(session)
            
            print("Creating sample tags...")
            tags = create_sample_tags(session)
            
            print("Creating sample boards...")
            boards = create_sample_boards(session, users)
            
            print("Creating sample pins...")
            pins = create_sample_pins(session, users, boards, tags)
            
            print("Creating following relationships...")
            create_following_relationships(session, users)
            
            print("Creating pin-board assignments...")
            pin_board_assignments(session, pins, boards, users)
            
            print("Creating sample interactions...")
            create_sample_interactions(session, users, pins)
            
            print("Creating sample likes and saves...")
            create_sample_likes_saves(session, users, pins)
            
            print("Database migrations completed successfully!")
            
            # Clear cache
            cache_manager.redis_client.flushdb()
            print("Cache cleared!")
            
    except Exception as e:
        print(f"Migration error: {e}")
        raise

def reset_database():
    """Reset database and run fresh migrations"""
    try:
        print("Dropping existing tables...")
        db_manager.drop_tables()
        
        print("Creating new tables...")
        db_manager.create_tables()
        
        print("Running migrations...")
        run_migrations()
        
        print("Database reset completed!")
        
    except Exception as e:
        print(f"Database reset error: {e}")
        raise

if __name__ == "__main__":
    # Initialize database connection
    db_manager.initialize()
    
    # Run migrations
    run_migrations()
