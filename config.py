import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///devices.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'firmware')
    SECRET_KEY = 'your-secret-key-here'
