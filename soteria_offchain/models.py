from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
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


class EcoAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(256), nullable=False)
    points = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='eco_actions')
