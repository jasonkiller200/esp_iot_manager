from app import db
from datetime import datetime, timezone, timedelta

TAIPEI_TZ = timezone(timedelta(hours=8))


def get_taipei_time():
    return datetime.now(TAIPEI_TZ)


class DataStream(db.Model):
    """Virtual Pin 數據流定義 (類似 Blynk Datastream)"""

    id = db.Column(db.Integer, primary_key=True)
    device_mac = db.Column(db.String(20), db.ForeignKey("device.mac"), nullable=False)
    pin = db.Column(db.String(10), nullable=False)  # 如 "V0", "V1", "V2"
    name = db.Column(db.String(50))  # 如 "Temperature", "Humidity"
    data_type = db.Column(db.String(20), default="double")  # double, integer, string
    min_value = db.Column(db.Float, default=0)
    max_value = db.Column(db.Float, default=100)
    unit = db.Column(db.String(20))  # 如 "°C", "%", "lux"
    color = db.Column(db.String(20), default="#667eea")  # 顯示顏色

    __table_args__ = (db.UniqueConstraint("device_mac", "pin", name="_device_pin_uc"),)

    def __repr__(self):
        return f"<DataStream {self.device_mac}:{self.pin}>"


class DataPoint(db.Model):
    """時間序列數據點 (類似 Blynk 數據存儲)"""

    id = db.Column(db.Integer, primary_key=True)
    device_mac = db.Column(db.String(20), db.ForeignKey("device.mac"), nullable=False)
    pin = db.Column(db.String(10), nullable=False)
    value = db.Column(db.String(100))  # 存為字串以支援多種類型
    timestamp = db.Column(db.DateTime, default=get_taipei_time, index=True)

    __table_args__ = (
        db.Index("idx_datapoint_device_pin_ts", "device_mac", "pin", "timestamp"),
    )

    def __repr__(self):
        return f"<DataPoint {self.device_mac}:{self.pin}={self.value}>"


class HourlyAggregate(db.Model):
    """小時級聚合數據（長期保存層）"""

    id = db.Column(db.Integer, primary_key=True)
    device_mac = db.Column(db.String(20), db.ForeignKey("device.mac"), nullable=False)
    pin = db.Column(db.String(10), nullable=False)
    hour_bucket = db.Column(db.DateTime, nullable=False, index=True)

    count = db.Column(db.Integer, default=0)
    min_value = db.Column(db.Float)
    max_value = db.Column(db.Float)
    avg_value = db.Column(db.Float)
    last_value = db.Column(db.String(100))

    __table_args__ = (
        db.UniqueConstraint(
            "device_mac", "pin", "hour_bucket", name="_device_pin_hour_uc"
        ),
        db.Index("idx_hourly_device_pin_bucket", "device_mac", "pin", "hour_bucket"),
    )

    def __repr__(self):
        return f"<HourlyAggregate {self.device_mac}:{self.pin}@{self.hour_bucket}>"
