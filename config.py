import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///devices.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'firmware')
    SECRET_KEY = 'your-secret-key-here'
    
    # MQTT 設定
    MQTT_BROKER_HOST = 'localhost'
    MQTT_BROKER_PORT = 1883
    MQTT_USERNAME = None  # 開發階段可為 None
    MQTT_PASSWORD = None
