#!/usr/bin/env python3
"""
Database Table Creation Script
Creates PostgreSQL tables for Pinterest Clone
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_tables():
    """Create all database tables"""
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')
    
    # Parse database URL
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
    if not match:
        print("❌ Invalid DATABASE_URL format")
        return
    
    username, password, host, port, database = match.groups()
    
    try:
        # Connect to PostgreSQL
        print(f"🔗 Connecting to PostgreSQL at {host}:{port}/{database}")
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL successfully!")
        
        # Create tables
        print("\n📋 Creating tables...")
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(100) NOT NULL,
                bio TEXT,
                avatar_url VARCHAR(500),
                is_active BOOLEAN DEFAULT TRUE,
                is_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """)
        print("✅ Created users table")
        
        # Tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                category VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
        """)
        print("✅ Created tags table")
        
        # Boards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS boards (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                creator_id INTEGER REFERENCES users(id),
                category VARCHAR(50),
                is_private BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_boards_creator ON boards(creator_id);
            CREATE INDEX IF NOT EXISTS idx_boards_category ON boards(category);
        """)
        print("✅ Created boards table")
        
        # Pins table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pins (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                image_url VARCHAR(500) NOT NULL,
                link VARCHAR(500),
                creator_id INTEGER REFERENCES users(id) NOT NULL,
                category VARCHAR(50),
                width INTEGER,
                height INTEGER,
                is_public BOOLEAN DEFAULT TRUE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_pins_creator ON pins(creator_id);
            CREATE INDEX IF NOT EXISTS idx_pins_category ON pins(category);
            CREATE INDEX IF NOT EXISTS idx_pins_created ON pins(created_at);
        """)
        print("✅ Created pins table")
        
        # Likes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                pin_id INTEGER REFERENCES pins(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, pin_id)
            );
            CREATE INDEX IF NOT EXISTS idx_likes_user ON likes(user_id);
            CREATE INDEX IF NOT EXISTS idx_likes_pin ON likes(pin_id);
        """)
        print("✅ Created likes table")
        
        # Saves table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saves (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                pin_id INTEGER REFERENCES pins(id),
                board_id INTEGER REFERENCES boards(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, pin_id)
            );
            CREATE INDEX IF NOT EXISTS idx_saves_user ON saves(user_id);
            CREATE INDEX IF NOT EXISTS idx_saves_pin ON saves(pin_id);
            CREATE INDEX IF NOT EXISTS idx_saves_board ON saves(board_id);
        """)
        print("✅ Created saves table")
        
        # Comments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                pin_id INTEGER REFERENCES pins(id),
                content TEXT NOT NULL,
                parent_id INTEGER REFERENCES comments(id),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_comments_user ON comments(user_id);
            CREATE INDEX IF NOT EXISTS idx_comments_pin ON comments(pin_id);
            CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id);
        """)
        print("✅ Created comments table")
        
        # Interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                pin_id INTEGER REFERENCES pins(id),
                interaction_type VARCHAR(20) NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_interactions_user ON interactions(user_id);
            CREATE INDEX IF NOT EXISTS idx_interactions_pin ON interactions(pin_id);
            CREATE INDEX IF NOT EXISTS idx_interactions_type ON interactions(interaction_type);
            CREATE INDEX IF NOT EXISTS idx_interactions_created ON interactions(created_at);
        """)
        print("✅ Created interactions table")
        
        # Junction tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_followers (
                follower_id INTEGER REFERENCES users(id),
                following_id INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (follower_id, following_id)
            );
            CREATE INDEX IF NOT EXISTS idx_user_followers_follower ON user_followers(follower_id);
            CREATE INDEX IF NOT EXISTS idx_user_followers_following ON user_followers(following_id);
        """)
        print("✅ Created user_followers table")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_boards (
                user_id INTEGER REFERENCES users(id),
                board_id INTEGER REFERENCES boards(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, board_id)
            );
            CREATE INDEX IF NOT EXISTS idx_user_boards_user ON user_boards(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_boards_board ON user_boards(board_id);
        """)
        print("✅ Created user_boards table")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pin_boards (
                pin_id INTEGER REFERENCES pins(id),
                board_id INTEGER REFERENCES boards(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (pin_id, board_id)
            );
            CREATE INDEX IF NOT EXISTS idx_pin_boards_pin ON pin_boards(pin_id);
            CREATE INDEX IF NOT EXISTS idx_pin_boards_board ON pin_boards(board_id);
        """)
        print("✅ Created pin_boards table")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pin_tags (
                pin_id INTEGER REFERENCES pins(id),
                tag_id INTEGER REFERENCES tags(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (pin_id, tag_id)
            );
            CREATE INDEX IF NOT EXISTS idx_pin_tags_pin ON pin_tags(pin_id);
            CREATE INDEX IF NOT EXISTS idx_pin_tags_tag ON pin_tags(tag_id);
        """)
        print("✅ Created pin_tags table")
        
        # Commit changes
        conn.commit()
        print("\n🎉 All tables created successfully!")
        
        # Insert sample data
        print("\n📝 Inserting sample data...")
        
        # Sample users
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, name, bio, avatar_url, is_verified) VALUES
            ('alice_creative', 'alice@example.com', 'hash123', 'Alice Johnson', 'DIY enthusiast | Home decor lover', 'https://picsum.photos/200/200?random=alice', TRUE),
            ('bob_foodie', 'bob@example.com', 'hash123', 'Bob Smith', 'Chef | Recipe developer', 'https://picsum.photos/200/200?random=bob', TRUE),
            ('charlie_travel', 'charlie@example.com', 'hash123', 'Charlie Brown', 'Travel blogger | Adventure seeker', 'https://picsum.photos/200/200?random=charlie', TRUE)
            ON CONFLICT (username) DO NOTHING;
        """)
        print("✅ Inserted sample users")
        
        # Sample tags
        cursor.execute("""
            INSERT INTO tags (name, category) VALUES
            ('diy', 'craft'), ('craft', 'craft'), ('home-decor', 'home'),
            ('recipe', 'food'), ('cooking', 'food'), ('baking', 'food'),
            ('travel', 'travel'), ('photography', 'travel'),
            ('fashion', 'fashion'), ('style', 'fashion'),
            ('fitness', 'fitness'), ('yoga', 'fitness'),
            ('technology', 'tech'), ('gadgets', 'tech'),
            ('art', 'art'), ('painting', 'art'),
            ('music', 'music'), ('guitar', 'music')
            ON CONFLICT (name) DO NOTHING;
        """)
        print("✅ Inserted sample tags")
        
        # Sample boards
        cursor.execute("""
            INSERT INTO boards (name, description, creator_id, category) VALUES
            ('DIY Projects', 'Collection of DIY ideas', 1, 'craft'),
            ('Recipe Collection', 'Best recipes', 2, 'food'),
            ('Travel Inspiration', 'Travel photos and tips', 3, 'travel')
            ON CONFLICT DO NOTHING;
        """)
        print("✅ Inserted sample boards")
        
        # Sample pins
        cursor.execute("""
            INSERT INTO pins (title, description, image_url, creator_id, category, width, height) VALUES
            ('DIY Wall Art Ideas', 'Creative DIY projects for home walls', 'https://picsum.photos/400/500?random=1', 1, 'craft', 400, 500),
            ('Chocolate Chip Cookies', 'Best chocolate chip cookie recipe', 'https://picsum.photos/400/450?random=2', 2, 'food', 400, 450),
            ('Sunset Photography Tips', 'How to take amazing travel photos', 'https://picsum.photos/400/350?random=3', 3, 'travel', 400, 350)
            ON CONFLICT DO NOTHING;
        """)
        print("✅ Inserted sample pins")
        
        conn.commit()
        print("\n🎊 Sample data inserted successfully!")
        
        # Show table info
        print("\n📊 Database Statistics:")
        cursor.execute("""
            SELECT 
                'users' as table_name, COUNT(*) as count FROM users
            UNION ALL SELECT 
                'pins' as table_name, COUNT(*) as count FROM pins
            UNION ALL SELECT 
                'boards' as table_name, COUNT(*) as count FROM boards
            UNION ALL SELECT 
                'tags' as table_name, COUNT(*) as count FROM tags
            UNION ALL SELECT 
                'likes' as table_name, COUNT(*) as count FROM likes
            UNION ALL SELECT 
                'saves' as table_name, COUNT(*) as count FROM saves;
        """)
        
        results = cursor.fetchall()
        for table_name, count in results:
            print(f"  📋 {table_name}: {count} records")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔌 Database connection closed")
    
    return True

if __name__ == "__main__":
    print("🚀 Pinterest Clone Database Setup")
    print("=" * 40)
    
    success = create_tables()
    
    if success:
        print("\n✅ Database setup completed successfully!")
        print("\n🌐 You can now start the application:")
        print("   cd src")
        print("   python3 main.py")
    else:
        print("\n❌ Database setup failed!")
        print("   Please check your database connection and try again.")
