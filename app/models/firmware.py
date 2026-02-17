from app import db
from datetime import datetime


class Firmware(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    chip_type = db.Column(db.String(20))
    description = db.Column(db.String(200))
    uploaded_at = db.Column(db.DateTime, default=datetime.now)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Firmware {self.version} ({self.chip_type})>"
