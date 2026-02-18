from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models.device import Device
from app.models.datastream import DataStream, DataPoint
from datetime import datetime, timezone, timedelta
import json

TAIPEI_TZ = timezone(timedelta(hours=8))

blynk_bp = Blueprint("blynk", __name__)


# ==================== Blynk 相容 API ====================

@blynk_bp.route("/<device_token>/update/<pin>", methods=["GET"])
def blynk_update_pin(device_token, pin):
    """
    Blynk API: 更新 Virtual Pin 值
    GET /blynk/{token}/update/V0?value=25.5
    """
    value = request.args.get('value')
    if not value:
        return jsonify({"error": "No value provided"}), 400
    
    device = Device.query.filter_by(mac=device_token).first()
    if not device:
        # 自動建立設備
        device = Device(mac=device_token)
        db.session.add(device)
        db.session.commit()
    
    # 確保 DataStream 存在
    datastream = DataStream.query.filter_by(device_mac=device.mac, pin=pin).first()
    if not datastream:
        datastream = DataStream(device_mac=device.mac, pin=pin, name=pin)
        db.session.add(datastream)
    
    # 儲存數據點
    data_point = DataPoint(device_mac=device.mac, pin=pin, value=value)
    db.session.add(data_point)
    
    # 更新設備最後上線時間
    device.last_seen = datetime.now(TAIPEI_TZ)
    
    db.session.commit()
    
    print(f"[Blynk API] {device_token}/{pin} = {value}")
    
    return jsonify({"success": True})


@blynk_bp.route("/<device_token>/get/<pin>", methods=["GET"])
def blynk_get_pin(device_token, pin):
    """
    Blynk API: 讀取 Virtual Pin 最新值
    GET /blynk/{token}/get/V0
    返回: ["25.5"]
    """
    device = Device.query.filter_by(mac=device_token).first()
    if not device:
        return jsonify([])
    
    latest = DataPoint.query.filter_by(
        device_mac=device.mac, 
        pin=pin
    ).order_by(DataPoint.timestamp.desc()).first()
    
    if not latest:
        return jsonify([])
    
    return jsonify([latest.value])


@blynk_bp.route("/<device_token>/data/<pin>", methods=["GET"])
def blynk_get_data(device_token, pin):
    """
    Blynk API: 讀取歷史數據
    GET /blynk/{token}/data/V0?period=day&granularityType=raw
    
    參數:
    - period: hour, day, week, month (預設 day)
    - granularityType: raw, minute, hour (預設 raw)
    - limit: 最多回傳筆數 (預設 1000)
    """
    device = Device.query.filter_by(mac=device_token).first()
    if not device:
        return jsonify([])
    
    period = request.args.get('period', 'day')
    granularity = request.args.get('granularityType', 'raw')
    limit = int(request.args.get('limit', 1000))
    
    # 計算時間範圍
    now = datetime.now(TAIPEI_TZ)
    period_map = {
        'hour': timedelta(hours=1),
        'day': timedelta(days=1),
        'week': timedelta(weeks=1),
        'month': timedelta(days=30)
    }
    start_time = now - period_map.get(period, timedelta(days=1))
    
    # 查詢數據
    query = DataPoint.query.filter(
        DataPoint.device_mac == device.mac,
        DataPoint.pin == pin,
        DataPoint.timestamp >= start_time
    ).order_by(DataPoint.timestamp.asc()).limit(limit)
    
    data_points = query.all()
    
    # Blynk 格式: [[timestamp_ms, value], ...]
    result = []
    for dp in data_points:
        timestamp_ms = int(dp.timestamp.timestamp() * 1000)
        try:
            value = float(dp.value)
        except ValueError:
            value = dp.value
        result.append([timestamp_ms, value])
    
    return jsonify(result)


@blynk_bp.route("/<device_token>/update", methods=["GET", "POST"])
def blynk_batch_update(device_token):
    """
    Blynk API: 批量更新多個 Pin
    GET /blynk/{token}/update?V0=25.5&V1=60&V2=hello
    POST /blynk/{token}/update with JSON body
    """
    device = Device.query.filter_by(mac=device_token).first()
    if not device:
        device = Device(mac=device_token)
        db.session.add(device)
        db.session.commit()
    
    # 支援 GET 和 POST
    if request.method == 'GET':
        pin_values = request.args.to_dict()
    else:
        pin_values = request.json or {}
    
    count = 0
    for pin, value in pin_values.items():
        if not pin.startswith('V'):
            continue
        
        # 確保 DataStream 存在
        datastream = DataStream.query.filter_by(device_mac=device.mac, pin=pin).first()
        if not datastream:
            datastream = DataStream(device_mac=device.mac, pin=pin, name=pin)
            db.session.add(datastream)
        
        # 儲存數據點
        data_point = DataPoint(device_mac=device.mac, pin=pin, value=str(value))
        db.session.add(data_point)
        count += 1
    
    # 更新設備最後上線時間
    device.last_seen = datetime.now(TAIPEI_TZ)
    db.session.commit()
    
    print(f"[Blynk API] {device_token} batch updated {count} pins")
    
    return jsonify({"success": True, "pins_updated": count})


@blynk_bp.route("/<device_token>/project", methods=["GET"])
def blynk_get_project(device_token):
    """
    Blynk API: 獲取設備的所有 Datastream 定義
    返回設備的 Virtual Pin 配置
    """
    device = Device.query.filter_by(mac=device_token).first()
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    datastreams = DataStream.query.filter_by(device_mac=device.mac).all()
    
    pins = []
    for ds in datastreams:
        pins.append({
            "pin": ds.pin,
            "name": ds.name,
            "dataType": ds.data_type,
            "min": ds.min_value,
            "max": ds.max_value,
            "unit": ds.unit
        })
    
    return jsonify({
        "id": device.id,
        "name": device.mac,
        "dataStreams": pins
    })


# ==================== 管理 API (非 Blynk 標準) ====================

@blynk_bp.route("/admin/datastream", methods=["POST"])
def create_datastream():
    """
    管理 API: 創建/更新 DataStream 定義
    POST /blynk/admin/datastream
    Body: {
        "device_mac": "AA:BB:CC:DD:EE:FF",
        "pin": "V0",
        "name": "Temperature",
        "data_type": "double",
        "min": 0,
        "max": 100,
        "unit": "°C"
    }
    """
    data = request.json
    
    if not data.get('device_mac') or not data.get('pin'):
        return jsonify({"error": "device_mac and pin are required"}), 400
    
    datastream = DataStream.query.filter_by(
        device_mac=data['device_mac'],
        pin=data['pin']
    ).first()
    
    if not datastream:
        datastream = DataStream()
        datastream.device_mac = data['device_mac']
        datastream.pin = data['pin']
        db.session.add(datastream)
    
    datastream.name = data.get('name', datastream.pin)
    datastream.data_type = data.get('data_type', 'double')
    datastream.min_value = data.get('min', 0)
    datastream.max_value = data.get('max', 100)
    datastream.unit = data.get('unit', '')
    
    db.session.commit()
    
    return jsonify({"success": True, "id": datastream.id})


@blynk_bp.route("/admin/datastreams/<device_mac>", methods=["GET"])
def list_datastreams(device_mac):
    """
    管理 API: 列出設備的所有 DataStream
    GET /blynk/admin/datastreams/AA:BB:CC:DD:EE:FF
    """
    datastreams = DataStream.query.filter_by(device_mac=device_mac).all()
    
    result = []
    for ds in datastreams:
        result.append({
            "id": ds.id,
            "pin": ds.pin,
            "name": ds.name,
            "data_type": ds.data_type,
            "min": ds.min_value,
            "max": ds.max_value,
            "unit": ds.unit
        })
    
    return jsonify(result)


@blynk_bp.route("/admin/data/stats/<device_mac>/<pin>", methods=["GET"])
def get_data_stats(device_mac, pin):
    """
    管理 API: 獲取數據統計
    GET /blynk/admin/data/stats/AA:BB:CC:DD:EE:FF/V0?hours=24
    """
    hours = int(request.args.get('hours', 24))
    cutoff = datetime.now(TAIPEI_TZ) - timedelta(hours=hours)
    
    points = DataPoint.query.filter(
        DataPoint.device_mac == device_mac,
        DataPoint.pin == pin,
        DataPoint.timestamp >= cutoff
    ).all()
    
    if not points:
        return jsonify({
            "count": 0,
            "min": None,
            "max": None,
            "avg": None
        })
    
    values = []
    for p in points:
        try:
            values.append(float(p.value))
        except ValueError:
            pass
    
    if not values:
        return jsonify({
            "count": len(points),
            "min": None,
            "max": None,
            "avg": None
        })
    
    return jsonify({
        "count": len(points),
        "min": min(values),
        "max": max(values),
        "avg": sum(values) / len(values),
        "latest": values[-1] if values else None
    })
