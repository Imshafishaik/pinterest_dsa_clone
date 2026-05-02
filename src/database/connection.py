import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
import redis
import logging
from contextlib import contextmanager

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/pinterest_db')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    
    def __init__(self, database_url=None, redis_url=None):
        self.database_url = database_url or DATABASE_URL
        self.redis_url = redis_url or REDIS_URL
        self.engine = None
        self.SessionLocal = None
        self.redis_client = None
        
    def initialize(self):
        try:
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=os.getenv('SQL_DEBUG', 'False').lower() == 'true'
            )
            
            self.SessionLocal = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            )
            
            logger.info("PostgreSQL connection established")
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            self.redis_client.ping()
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_redis(self):
        return self.redis_client
    
    def create_tables(self):
        try:
            from .models import Base
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Table creation failed: {e}")
            raise
    
    def drop_tables(self):
        try:
            from .models import Base
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped")
        except Exception as e:
            logger.error(f"Table drop failed: {e}")
            raise
    
    def health_check(self):
        health = {
            'database': False,
            'redis': False,
            'errors': []
        }
        
        try:
            with self.get_session() as session:
                session.execute('SELECT 1')
                health['database'] = True
        except Exception as e:
            health['errors'].append(f"Database error: {e}")
        
        try:
            self.redis_client.ping()
            health['redis'] = True
        except Exception as e:
            health['errors'].append(f"Redis error: {e}")
        
        return health

db_manager = DatabaseManager()

def get_db():
    return db_manager.get_session()

def get_redis():
    return db_manager.get_redis()

class CacheManager:
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or db_manager.redis_client
        self.default_ttl = 3600
    
    def get(self, key):
        try:
            return self.redis.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key, value, ttl=None):
        try:
            ttl = ttl or self.default_ttl
            return self.redis.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key):
        try:
            return self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def exists(self, key):
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    def increment(self, key, amount=1):
        try:
            return self.redis.incr(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return None
    
    def get_many(self, keys):
        try:
            return self.redis.mget(keys)
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return []
    
    def set_many(self, mapping, ttl=None):
        try:
            ttl = ttl or self.default_ttl
            pipe = self.redis.pipeline()
            for key, value in mapping.items():
                pipe.setex(key, ttl, value)
            return pipe.execute()
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False

cache_manager = CacheManager()

CACHE_KEYS = {
    'PIN': 'pin:{id}',
    'USER': 'user:{id}',
    'BOARD': 'board:{id}',
    'USER_FEED': 'feed:user:{id}',
    'TRENDING': 'trending',
    'SEARCH_RESULTS': 'search:{query}',
    'RECOMMENDATIONS': 'recommendations:user:{id}',
    'PIN_STATS': 'stats:pin:{id}',
    'USER_STATS': 'stats:user:{id}'
}

def invalidate_cache_pattern(pattern):
    try:
        keys = db_manager.redis_client.keys(pattern)
        if keys:
            db_manager.redis_client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching {pattern}")
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")

class Config:
    
    SQL_DEBUG = os.getenv('SQL_DEBUG', 'False').lower() == 'true'
    DATABASE_URL = DATABASE_URL
    REDIS_URL = REDIS_URL
    
    CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
    
    API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '100/hour')
    
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '10485760'))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')

class DevelopmentConfig(Config):
    SQL_DEBUG = True
    DATABASE_URL = 'sqlite:///pinterest_dev.db'
    REDIS_URL = 'redis://localhost:6379/1'

class TestingConfig(Config):
    SQL_DEBUG = False
    DATABASE_URL = 'sqlite:///:memory:'
    REDIS_URL = 'redis://localhost:6379/15'
    CACHE_TTL = 60

class ProductionConfig(Config):
    SQL_DEBUG = False

configs = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    return configs.get(env, DevelopmentConfig)
