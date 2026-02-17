from app import db
from datetime import datetime, timezone, timedelta

TAIPEI_TZ = timezone(timedelta(hours=8))


def get_taipei_time():
    return datetime.now(TAIPEI_TZ)


class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mac = db.Column(db.String(20), unique=True, nullable=False)
    ip = db.Column(db.String(20))
    version = db.Column(db.String(20))
    last_seen = db.Column(db.DateTime, default=get_taipei_time)
    chip_type = db.Column(db.String(20))
    pending_update = db.Column(db.Boolean, default=False)
    target_version = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<Device {self.mac} @ {self.ip}>"
