from app import db
from datetime import datetime, timezone, timedelta

TAIPEI_TZ = timezone(timedelta(hours=8))


def get_taipei_time():
    return datetime.now(TAIPEI_TZ)


class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mac = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(50))  # 設備名稱 (自定義)
    ip = db.Column(db.String(20))
    version = db.Column(db.String(20))
    last_seen = db.Column(db.DateTime, default=get_taipei_time)
    chip_type = db.Column(db.String(20))
    pending_update = db.Column(db.Boolean, default=False)
    target_version = db.Column(db.String(20), nullable=True)

    def is_online(self, timeout_minutes=5):
        """判斷設備是否在線（預設5分鐘內有活動視為在線）"""
        if not self.last_seen:
            return False
        
        # 確保 last_seen 有時區資訊
        if self.last_seen.tzinfo is None:
            last_seen = self.last_seen.replace(tzinfo=TAIPEI_TZ)
        else:
            last_seen = self.last_seen
        
        now = datetime.now(TAIPEI_TZ)
        return (now - last_seen).total_seconds() < timeout_minutes * 60

    def __repr__(self):
        return f"<Device {self.mac} @ {self.ip}>"
