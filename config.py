import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///devices.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(os.getcwd(), "firmware"))
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    # 寫入/控制操作保護 Token
    WRITE_API_TOKEN = os.getenv("WRITE_API_TOKEN", "")

    # MQTT 設定
    MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_USERNAME = os.getenv("MQTT_USERNAME")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
    MQTT_FLUSH_BATCH_SIZE = int(os.getenv("MQTT_FLUSH_BATCH_SIZE", "100"))
    MQTT_FLUSH_INTERVAL_SEC = int(os.getenv("MQTT_FLUSH_INTERVAL_SEC", "2"))

    # 控制命令白名單（逗號分隔，例如 V10,V11,system）
    CONTROL_PIN_WHITELIST = os.getenv("CONTROL_PIN_WHITELIST", "")

    @classmethod
    def validate_security(cls):
        warnings = []
        if cls.ENV == "production":
            if not cls.SECRET_KEY or cls.SECRET_KEY == "change-this-in-production":
                warnings.append("SECRET_KEY is not set securely for production")
            if not cls.WRITE_API_TOKEN:
                warnings.append("WRITE_API_TOKEN is empty in production")
        return warnings
