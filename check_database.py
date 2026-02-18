"""檢查資料庫數據"""
from app import create_app, db
from app.models.datastream import DataPoint, DataStream
from app.models.device import Device

app = create_app()

with app.app_context():
    print("=" * 50)
    print("🎯 資料庫統計")
    print("=" * 50)
    print(f"  設備數: {Device.query.count()}")
    print(f"  數據流數: {DataStream.query.count()}")
    print(f"  數據點數: {DataPoint.query.count()}")
    
    print("\n" + "=" * 50)
    print("📊 最新數據 (前 10 筆)")
    print("=" * 50)
    
    points = DataPoint.query.order_by(DataPoint.timestamp.desc()).limit(10).all()
    for p in points:
        print(f"  {p.device_mac}/{p.pin} = {p.value} @ {p.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "=" * 50)
    print("📡 設備列表")
    print("=" * 50)
    
    devices = Device.query.all()
    for d in devices:
        print(f"  MAC: {d.mac}")
        print(f"  IP: {d.ip}")
        print(f"  最後上線: {d.last_seen}")
        print(f"  芯片: {d.chip_type}")
        print()
