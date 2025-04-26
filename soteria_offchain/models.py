from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model,UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    planet_credits = db.Column(db.Float, default=0.0)
    social_status = db.Column(db.Float, default=0.0)
    is_citizen = db.Column(db.Boolean, default=False)
    soteria_id = db.Column(db.String(20), unique=True)
    position = db.Column(db.String(64))
    image_url = db.Column(db.String(256))
    certificate_path = db.Column(db.String(255))
    reputation = db.Column(db.Integer, default=0)

    # Relationships
    eco_actions = db.relationship('EcoAction', backref='user', lazy=True)
    reviews = db.relationship('EcoActionReview', backref='reviewer', lazy=True)

    def __repr__(self):
        return f'<User {self.name}>'


class EcoAction(db.Model):
    __tablename__ = 'eco_action'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(256), nullable=False)
    points = db.Column(db.Float, nullable=False)
    proof_photo = db.Column(db.String(255))  # Optional proof photo
    geo_location = db.Column(db.String(255))  # Optional GPS location
    status = db.Column(db.String(50), default='Pending')  # Pending, Approved, Rejected
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    reviews = db.relationship('EcoActionReview', backref='eco_action', lazy=True)

    def __repr__(self):
        return f'<EcoAction {self.id} - {self.description[:20]}>'


class EcoActionReview(db.Model):
    __tablename__ = 'eco_action_review'

    id = db.Column(db.Integer, primary_key=True)
    decision = db.Column(db.String(20), nullable=False)  # Approve, Reject, Request Info
    comment = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Keys
    eco_action_id = db.Column(db.Integer, db.ForeignKey('eco_action.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<EcoActionReview {self.id} - {self.decision}>'
