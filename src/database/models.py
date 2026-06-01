"""
Database Models for Pinterest Clone
SQLAlchemy models for PostgreSQL database
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

# Many-to-many relationship tables
user_followers = Table(
    'user_followers',
    Base.metadata,
    Column('follower_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('following_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('created_at', DateTime, default=func.now())
)

user_boards = Table(
    'user_boards',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('board_id', Integer, ForeignKey('boards.id'), primary_key=True),
    Column('created_at', DateTime, default=func.now())
)

pin_boards = Table(
    'pin_boards',
    Base.metadata,
    Column('pin_id', Integer, ForeignKey('pins.id'), primary_key=True),
    Column('board_id', Integer, ForeignKey('boards.id'), primary_key=True),
    Column('created_at', DateTime, default=func.now())
)

pin_tags = Table(
    'pin_tags',
    Base.metadata,
    Column('pin_id', Integer, ForeignKey('pins.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
    Column('created_at', DateTime, default=func.now())
)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    bio = Column(Text)
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    created_pins = relationship("Pin", back_populates="creator")
    boards = relationship("Board", secondary=user_boards, back_populates="users")
    followers = relationship("User", 
                           secondary=user_followers,
                           primaryjoin=id==user_followers.c.following_id,
                           secondaryjoin=id==user_followers.c.follower_id,
                           back_populates="following")
    following = relationship("User",
                            secondary=user_followers,
                            primaryjoin=id==user_followers.c.follower_id,
                            secondaryjoin=id==user_followers.c.following_id,
                            back_populates="followers")
    likes = relationship("Like", back_populates="user")
    saves = relationship("Save", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Pin(Base):
    __tablename__ = 'pins'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    image_url = Column(String(500), nullable=False)
    link = Column(String(500))
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    category = Column(String(50), index=True)
    width = Column(Integer)
    height = Column(Integer)
    is_public = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="created_pins")
    boards = relationship("Board", secondary=pin_boards, back_populates="pins")
    tags = relationship("Tag", secondary=pin_tags, back_populates="pins")
    likes = relationship("Like", back_populates="pin")
    saves = relationship("Save", back_populates="pin")
    comments = relationship("Comment", back_populates="pin")
    
    # Computed properties
    @property
    def like_count(self):
        return len(self.likes) if self.likes else 0
    
    @property
    def save_count(self):
        return len(self.saves) if self.saves else 0
    
    @property
    def comment_count(self):
        return len(self.comments) if self.comments else 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image_url': self.image_url,
            'link': self.link,
            'creator_id': self.creator_id,
            'category': self.category,
            'width': self.width,
            'height': self.height,
            'is_public': self.is_public,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'like_count': self.like_count,
            'save_count': self.save_count,
            'comment_count': self.comment_count
        }

class Board(Base):
    __tablename__ = 'boards'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    category = Column(String(50), index=True)
    is_private = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    creator = relationship("User")
    users = relationship("User", secondary=user_boards, back_populates="boards")
    pins = relationship("Pin", secondary=pin_boards, back_populates="boards")
    
    @property
    def pin_count(self):
        return len(self.pins) if self.pins else 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'creator_id': self.creator_id,
            'category': self.category,
            'is_private': self.is_private,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'pin_count': self.pin_count
        }

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    category = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    pins = relationship("Pin", secondary=pin_tags, back_populates="tags")
    
    @property
    def pin_count(self):
        return len(self.pins) if self.pins else 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'pin_count': self.pin_count
        }

class Like(Base):
    __tablename__ = 'likes'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    pin_id = Column(Integer, ForeignKey('pins.id'), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="likes")
    pin = relationship("Pin", back_populates="likes")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'pin_id': self.pin_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Save(Base):
    __tablename__ = 'saves'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    pin_id = Column(Integer, ForeignKey('pins.id'), nullable=False, index=True)
    board_id = Column(Integer, ForeignKey('boards.id'))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="saves")
    pin = relationship("Pin", back_populates="saves")
    board = relationship("Board")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'pin_id': self.pin_id,
            'board_id': self.board_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Comment(Base):
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    pin_id = Column(Integer, ForeignKey('pins.id'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey('comments.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="comments")
    pin = relationship("Pin", back_populates="comments")
    parent = relationship("Comment", remote_side=[id])
    children = relationship("Comment")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'pin_id': self.pin_id,
            'content': self.content,
            'parent_id': self.parent_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Interaction(Base):
    __tablename__ = 'interactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    pin_id = Column(Integer, ForeignKey('pins.id'), nullable=False, index=True)
    interaction_type = Column(String(20), nullable=False, index=True)  # 'view', 'click', 'share'
    interaction_metadata = Column(Text)  # JSON metadata
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User")
    pin = relationship("Pin")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'pin_id': self.pin_id,
            'interaction_type': self.interaction_type,
            'metadata': self.interaction_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
