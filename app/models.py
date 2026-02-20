from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['argon2'], deprecated='auto')

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(128))
    bio = Column(String(500))
    image_url = Column(String(255))

    swipes_made = relationship('Swipe', foreign_keys='Swipe.swiper_id', backref='swiper')
    swipes_received = relationship('Swipe', foreign_keys='Swipe.swiped_id', backref='swiped')

    matches_as_user1 = relationship('Match', foreign_keys='Match.user1_id', backref='user1')
    matches_as_user2 = relationship('Match', foreign_keys='Match.user2_id', backref='user2')

    messages_sent = relationship('Message', foreign_keys='Message.sender_id', backref='sender')
    messages_received = relationship('Message', foreign_keys='Message.recipient_id', backref='recipient')

    def set_password(self, password):
        self.password_hash = pwd_context.hash(password)

    def check_password(self, password):
        return pwd_context.verify(password, self.password_hash)

class Swipe(Base):
    __tablename__ = 'swipe'
    id = Column(Integer, primary_key=True, index=True)
    swiper_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    swiped_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    is_like = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Match(Base):
    __tablename__ = 'match'
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user2_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    recipient_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    body = Column(String(1000), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
