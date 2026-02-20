from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    bio = db.Column(db.String(500))
    image_url = db.Column(db.String(255))

    swipes_made = db.relationship('Swipe', foreign_keys='Swipe.swiper_id', backref='swiper', lazy='dynamic')
    swipes_received = db.relationship('Swipe', foreign_keys='Swipe.swiped_id', backref='swiped', lazy='dynamic')

    matches_as_user1 = db.relationship('Match', foreign_keys='Match.user1_id', backref='user1', lazy='dynamic')
    matches_as_user2 = db.relationship('Match', foreign_keys='Match.user2_id', backref='user2', lazy='dynamic')

    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Swipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    swiper_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    swiped_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_like = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body = db.Column(db.String(1000), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
