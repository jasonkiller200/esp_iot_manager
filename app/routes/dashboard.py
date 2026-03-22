from flask import Blueprint, render_template, jsonify, request
from flask_socketio import emit
from app import db, socketio
from app.mqtt_manager import mqtt_manager
from app.auth import require_write_token
from app.models.device import Device
from app.models.datastream import DataStream, DataPoint, HourlyAggregate
from datetime import datetime, timezone, timedelta
from sqlalchemy import func
import json

dashboard_bp = Blueprint("dashboard", __name__)

TAIPEI_TZ = timezone(timedelta(hours=8))


@dashboard_bp.route("/")
def index():
    """儀表板首頁 - 顯示所有設備"""
    devices = Device.query.order_by(Device.last_seen.desc()).all()

    datastream_rows = db.session.query(DataStream.device_mac, DataStream.pin).all()
    device_pins = {}
    available_pins = set()
    for device_mac, pin in datastream_rows:
        device_pins.setdefault(device_mac, []).append(pin)
        available_pins.add(pin)

    for mac in device_pins:
        device_pins[mac] = sorted(set(device_pins[mac]))

    # 計算設備統計
    total_devices = len(devices)
    online_devices = sum(1 for d in devices if d.is_online())

    return render_template(
        "dashboard.html",
        devices=devices,
        device_pins=device_pins,
        available_pins=sorted(available_pins),
        total_devices=total_devices,
        online_devices=online_devices,
    )


@dashboard_bp.route("/device/<device_mac>")
def device_detail(device_mac):
    """設備詳細頁面 - 顯示即時數據和圖表"""
    device = Device.query.filter_by(mac=device_mac).first_or_404()
    devices = Device.query.order_by(Device.last_seen.desc()).all()
    datastreams = DataStream.query.filter_by(device_mac=device_mac).all()

    devices_json = [
        {
            "mac": d.mac,
            "name": d.name,
            "chip_type": d.chip_type,
        }
        for d in devices
    ]

    # 將 DataStream 轉換為可序列化的字典列表
    datastreams_json = [
        {
            "id": ds.id,
            "pin": ds.pin,
            "name": ds.name,
            "data_type": ds.data_type,
            "min_value": ds.min_value,
            "max_value": ds.max_value,
            "unit": ds.unit,
            "color": ds.color,
        }
        for ds in datastreams
    ]

    return render_template(
        "device_detail.html",
        device=device,
        devices=devices,
        devices_json=devices_json,
        datastreams=datastreams,
        datastreams_json=datastreams_json,
    )


@dashboard_bp.route("/api/devices")
def api_devices():
    """API: 獲取所有設備狀態"""
    devices = Device.query.all()
    datastream_rows = db.session.query(DataStream.device_mac, DataStream.pin).all()
    device_pins = {}
    for device_mac, pin in datastream_rows:
        device_pins.setdefault(device_mac, []).append(pin)

    result = []

    for device in devices:
        result.append(
            {
                "mac": device.mac,
                "name": device.name,
                "ip": device.ip,
                "version": device.version,
                "chip_type": device.chip_type,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                "is_online": device.is_online(),
                "pins": sorted(set(device_pins.get(device.mac, []))),
            }
        )

    return jsonify(result)


@dashboard_bp.route("/api/device/<device_mac>/datastreams")
def api_device_datastreams(device_mac):
    """API: 獲取設備的所有 DataStream"""
    datastreams = DataStream.query.filter_by(device_mac=device_mac).all()

    result = []
    for ds in datastreams:
        # 獲取最新值
        latest = (
            DataPoint.query.filter_by(device_mac=device_mac, pin=ds.pin)
            .order_by(DataPoint.timestamp.desc())
            .first()
        )

        result.append(
            {
                "id": ds.id,
                "pin": ds.pin,
                "name": ds.name,
                "data_type": ds.data_type,
                "min": ds.min_value,
                "max": ds.max_value,
                "unit": ds.unit,
                "color": ds.color,
                "latest_value": latest.value if latest else None,
                "latest_time": latest.timestamp.isoformat() if latest else None,
            }
        )

    return jsonify(result)


@dashboard_bp.route("/api/device/<device_mac>/data/<pin>")
def api_device_data(device_mac, pin):
    """API: 獲取指定 Pin 的歷史數據"""
    hours = int(request.args.get("hours", 1))
    limit = int(request.args.get("limit", 500))
    source = request.args.get("source", "raw")
    bucket_minutes = max(1, int(request.args.get("bucket_minutes", 5)))

    cutoff = datetime.now(TAIPEI_TZ) - timedelta(hours=hours)

    # 自動來源切換：長時段優先查詢小時聚合
    if source == "auto":
        source = "hourly" if hours > 24 else "raw"

    if source == "hourly":
        rows = (
            HourlyAggregate.query.filter(
                HourlyAggregate.device_mac == device_mac,
                HourlyAggregate.pin == pin,
                HourlyAggregate.hour_bucket >= cutoff,
            )
            .order_by(HourlyAggregate.hour_bucket.asc())
            .limit(limit)
            .all()
        )

        result = []
        for row in rows:
            result.append(
                {
                    "timestamp": row.hour_bucket.isoformat(),
                    "value": row.avg_value,
                    "count": row.count,
                    "min": row.min_value,
                    "max": row.max_value,
                    "last": row.last_value,
                }
            )
        return jsonify(result)

    data_points = (
        DataPoint.query.filter(
            DataPoint.device_mac == device_mac,
            DataPoint.pin == pin,
            DataPoint.timestamp >= cutoff,
        )
        .order_by(DataPoint.timestamp.asc())
        .limit(limit)
        .all()
    )

    def parse_value(raw_value):
        try:
            return float(raw_value)
        except (TypeError, ValueError):
            return None

    if source == "aggregated":
        buckets = {}
        for dp in data_points:
            numeric = parse_value(dp.value)
            if numeric is None:
                continue

            ts = dp.timestamp
            minute_slot = (ts.minute // bucket_minutes) * bucket_minutes
            bucket_ts = ts.replace(minute=minute_slot, second=0, microsecond=0)
            key = bucket_ts.isoformat()

            bucket = buckets.get(key)
            if bucket is None:
                buckets[key] = {
                    "timestamp": bucket_ts.isoformat(),
                    "sum": numeric,
                    "count": 1,
                }
            else:
                bucket["sum"] += numeric
                bucket["count"] += 1

        result = []
        for key in sorted(buckets.keys()):
            item = buckets[key]
            result.append(
                {
                    "timestamp": item["timestamp"],
                    "value": item["sum"] / item["count"],
                    "count": item["count"],
                }
            )
        return jsonify(result)

    result = []
    for dp in data_points:
        result.append({"timestamp": dp.timestamp.isoformat(), "value": dp.value})

    return jsonify(result)


@dashboard_bp.route("/api/device/<device_mac>/stats")
def api_device_stats(device_mac):
    """API: 獲取設備數據統計"""
    hours = int(request.args.get("hours", 24))
    cutoff = datetime.now(TAIPEI_TZ) - timedelta(hours=hours)

    # 獲取所有 DataStream
    datastreams = DataStream.query.filter_by(device_mac=device_mac).all()

    result = {}
    for ds in datastreams:
        points = DataPoint.query.filter(
            DataPoint.device_mac == device_mac,
            DataPoint.pin == ds.pin,
            DataPoint.timestamp >= cutoff,
        ).all()

        if not points:
            continue

        values = []
        for p in points:
            try:
                values.append(float(p.value))
            except ValueError:
                pass

        if values:
            result[ds.pin] = {
                "name": ds.name,
                "count": len(points),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "latest": values[-1],
            }

    return jsonify(result)


@dashboard_bp.route("/device/<device_mac>/edit", methods=["POST"])
@require_write_token()
def edit_device(device_mac):
    """編輯設備資訊"""
    device = Device.query.filter_by(mac=device_mac).first_or_404()
    data = request.json

    if "name" in data:
        device.name = data["name"]

    db.session.commit()
    return jsonify({"status": "ok", "name": device.name})


@dashboard_bp.route("/device/<device_mac>/delete", methods=["POST"])
@require_write_token()
def delete_device(device_mac):
    """刪除設備及其所有數據"""
    device = Device.query.filter_by(mac=device_mac).first_or_404()

    # 刪除關聯的數據點和數據流
    DataPoint.query.filter_by(device_mac=device_mac).delete()
    HourlyAggregate.query.filter_by(device_mac=device_mac).delete()
    DataStream.query.filter_by(device_mac=device_mac).delete()

    db.session.delete(device)
    db.session.commit()

    return jsonify({"status": "ok"})


@dashboard_bp.route("/admin/db-health", methods=["GET"])
def db_health():
    """簡易 DB 健康檢查（供維運與排程驗證）"""
    try:
        raw_count = DataPoint.query.count()
        hourly_count = HourlyAggregate.query.count()
        latest_raw = db.session.query(func.max(DataPoint.timestamp)).scalar()
        latest_hourly = db.session.query(func.max(HourlyAggregate.hour_bucket)).scalar()

        return jsonify(
            {
                "status": "ok",
                "raw_count": raw_count,
                "hourly_count": hourly_count,
                "latest_raw": latest_raw.isoformat() if latest_raw else None,
                "latest_hourly": latest_hourly.isoformat() if latest_hourly else None,
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@dashboard_bp.route("/datastream/<int:ds_id>/edit", methods=["POST"])
@require_write_token()
def edit_datastream(ds_id):
    """編輯數據流設定"""
    ds = DataStream.query.get_or_404(ds_id)
    data = request.json

    if "name" in data:
        ds.name = data["name"]
    if "unit" in data:
        ds.unit = data["unit"]
    if "color" in data:
        ds.color = data["color"]
    if "min_value" in data:
        ds.min_value = float(data["min_value"])
    if "max_value" in data:
        ds.max_value = float(data["max_value"])

    db.session.commit()
    return jsonify(
        {"status": "ok", "name": ds.name, "unit": ds.unit, "color": ds.color}
    )


@dashboard_bp.route("/device/<device_mac>/control", methods=["POST"])
@require_write_token()
def control_device(device_mac):
    """透過 MQTT 發送設備控制指令"""
    device = Device.query.filter_by(mac=device_mac).first_or_404()
    data = request.json or {}

    pin = (data.get("pin") or "").strip()
    value = data.get("value")

    if not pin:
        return jsonify({"status": "error", "message": "pin is required"}), 400

    if value is None:
        return jsonify({"status": "error", "message": "value is required"}), 400

    if not mqtt_manager.connected:
        return (
            jsonify({"status": "error", "message": "MQTT broker not connected"}),
            503,
        )

    ok = mqtt_manager.send_control_command(device.mac, pin, value)
    if not ok:
        return jsonify({"status": "error", "message": "failed to publish command"}), 500

    return jsonify(
        {
            "status": "ok",
            "message": "command sent",
            "topic": f"devices/{device.mac}/control/{pin}",
            "pin": pin,
            "value": value,
        }
    )


@dashboard_bp.route("/device/<device_mac>/reboot", methods=["POST"])
@require_write_token()
def reboot_device(device_mac):
    """透過 MQTT 發送設備重啟指令"""
    device = Device.query.filter_by(mac=device_mac).first_or_404()

    if not mqtt_manager.connected:
        return (
            jsonify({"status": "error", "message": "MQTT broker not connected"}),
            503,
        )

    topic = f"devices/{device.mac}/control/system"
    payload = json.dumps(
        {
            "action": "reboot",
            "requested_at": datetime.now(TAIPEI_TZ).isoformat(),
        }
    )

    ok = mqtt_manager.publish(topic, payload, qos=1)
    if not ok:
        return jsonify({"status": "error", "message": "failed to publish reboot"}), 500

    return jsonify(
        {
            "status": "ok",
            "message": "reboot command sent",
            "topic": topic,
        }
    )


@dashboard_bp.route("/live")
def live_dashboard():
    """即時全螢幕儀表板"""
    devices = Device.query.all()
    return render_template("live_dashboard.html", devices=devices)


# ==================== WebSocket Events ====================


@socketio.on("connect")
def handle_connect():
    """客戶端連接"""
    print("[WebSocket] Client connected")
    emit("status", {"status": "connected"})


@socketio.on("disconnect")
def handle_disconnect():
    """客戶端斷開"""
    print("[WebSocket] Client disconnected")


@socketio.on("subscribe_device")
def handle_subscribe_device(data):
    """訂閱設備數據更新"""
    device_mac = data.get("device_mac")
    print(f"[WebSocket] Client subscribed to device: {device_mac}")
    emit("subscribed", {"device_mac": device_mac})


@socketio.on("request_data")
def handle_request_data(data):
    """請求即時數據"""
    device_mac = data.get("device_mac")
    pin = data.get("pin")

    if not device_mac or not pin:
        return

    # 獲取最新數據點
    latest = (
        DataPoint.query.filter_by(device_mac=device_mac, pin=pin)
        .order_by(DataPoint.timestamp.desc())
        .first()
    )

    if latest:
        emit(
            "data_update",
            {
                "device_mac": device_mac,
                "pin": pin,
                "value": latest.value,
                "timestamp": latest.timestamp.isoformat(),
            },
        )


def broadcast_data_update(device_mac, pin, value):
    """廣播數據更新到所有連接的客戶端"""
    socketio.emit(
        "data_update",
        {
            "device_mac": device_mac,
            "pin": pin,
            "value": value,
            "timestamp": datetime.now(TAIPEI_TZ).isoformat(),
        },
        namespace="/",
    )


def broadcast_device_status(device_mac, status):
    """廣播設備狀態更新"""
    socketio.emit(
        "device_status",
        {
            "device_mac": device_mac,
            "status": status,
            "timestamp": datetime.now(TAIPEI_TZ).isoformat(),
        },
        namespace="/",
    )
