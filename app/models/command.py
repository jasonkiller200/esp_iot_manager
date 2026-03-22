from app import db
from datetime import datetime, timezone, timedelta
import uuid

TAIPEI_TZ = timezone(timedelta(hours=8))


def get_taipei_time():
    return datetime.now(TAIPEI_TZ)


class DeviceCommand(db.Model):
    """設備控制命令追蹤（Week 3 lifecycle）"""

    id = db.Column(db.Integer, primary_key=True)
    command_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    device_mac = db.Column(
        db.String(20), db.ForeignKey("device.mac"), nullable=False, index=True
    )

    command_type = db.Column(db.String(20), nullable=False, default="control")
    pin = db.Column(db.String(20))
    value = db.Column(db.String(255))

    status = db.Column(db.String(20), nullable=False, default="queued", index=True)
    requested_by = db.Column(db.String(64), default="api_token")
    error_message = db.Column(db.String(255))
    ack_event = db.Column(db.String(40))
    ack_message = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=get_taipei_time, index=True)
    sent_at = db.Column(db.DateTime)
    ack_at = db.Column(db.DateTime)
    timeout_at = db.Column(db.DateTime)

    __table_args__ = (
        db.Index(
            "idx_command_device_status_created", "device_mac", "status", "created_at"
        ),
    )

    @staticmethod
    def new_command_id():
        return str(uuid.uuid4())

    def to_dict(self):
        return {
            "command_id": self.command_id,
            "device_mac": self.device_mac,
            "command_type": self.command_type,
            "pin": self.pin,
            "value": self.value,
            "status": self.status,
            "ack_event": self.ack_event,
            "ack_message": self.ack_message,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "ack_at": self.ack_at.isoformat() if self.ack_at else None,
            "timeout_at": self.timeout_at.isoformat() if self.timeout_at else None,
        }
