from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from config import Config

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    # 初始化 MQTT Manager
    from app.mqtt_manager import mqtt_manager
    mqtt_manager.init_app(app)

    # 註冊 Blueprints (C: Controllers)
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.blynk_api import blynk_bp
    from app.routes.dashboard import dashboard_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(blynk_bp, url_prefix='/blynk')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    return app
