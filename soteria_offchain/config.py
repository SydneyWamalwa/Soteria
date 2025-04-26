import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-this-secret'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'soteria.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TREASURY_BALANCE = float(os.environ.get('TREASURY_BALANCE') or 10000)
    STIPEND_BASE = float(os.environ.get('STIPEND_BASE') or 100)
