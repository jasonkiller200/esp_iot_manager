"""
清理資料庫腳本
用於清除測試數據，重新開始測試
"""

from app import create_app, db
from app.models.device import Device
from app.models.datastream import DataStream, DataPoint

def clear_all_data():
    """清除所有設備和數據"""
    app = create_app()
    with app.app_context():
        print("\n" + "="*60)
        print(" 🗑️  清理資料庫")
        print("="*60)
        
        # 顯示清理前的統計
        device_count = Device.query.count()
        datastream_count = DataStream.query.count()
        datapoint_count = DataPoint.query.count()
        
        print("\n📊 清理前統計：")
        print(f"   設備數量: {device_count}")
        print(f"   DataStream 數量: {datastream_count}")
        print(f"   DataPoint 數量: {datapoint_count}")
        
        if device_count == 0 and datastream_count == 0 and datapoint_count == 0:
            print("\n✅ 資料庫已經是空的！")
            return
        
        # 確認清理
        print("\n⚠️  即將清除所有數據！")
        confirm = input("確定要繼續嗎？(yes/no): ")
        
        if confirm.lower() not in ['yes', 'y']:
            print("\n❌ 取消清理操作")
            return
        
        # 清理數據（按順序刪除避免外鍵約束）
        print("\n🗑️  清理中...")
        
        # 1. 刪除 DataPoint（數據點）
        deleted_points = DataPoint.query.delete()
        print(f"   ✓ 刪除 {deleted_points} 個數據點")
        
        # 2. 刪除 DataStream（數據流）
        deleted_streams = DataStream.query.delete()
        print(f"   ✓ 刪除 {deleted_streams} 個數據流")
        
        # 3. 刪除 Device（設備）
        deleted_devices = Device.query.delete()
        print(f"   ✓ 刪除 {deleted_devices} 個設備")
        
        # 提交更改
        db.session.commit()
        
        # 驗證清理結果
        print("\n📊 清理後統計：")
        print(f"   設備數量: {Device.query.count()}")
        print(f"   DataStream 數量: {DataStream.query.count()}")
        print(f"   DataPoint 數量: {DataPoint.query.count()}")
        
        print("\n" + "="*60)
        print(" ✅ 資料庫清理完成！")
        print("="*60)
        print("\n💡 提示：")
        print("   - 儀表板現在是空的")
        print("   - 當設備連線後會自動註冊")
        print("   - 數據會自動開始收集")
        print()

def clear_specific_device(mac_address):
    """清除特定設備的數據"""
    app = create_app()
    with app.app_context():
        device = Device.query.filter_by(mac=mac_address).first()
        
        if not device:
            print(f"\n❌ 找不到設備: {mac_address}")
            return
        
        print(f"\n🗑️  清理設備: {mac_address}")
        
        # 刪除相關數據
        points = DataPoint.query.filter_by(device_mac=mac_address).delete()
        streams = DataStream.query.filter_by(device_mac=mac_address).delete()
        db.session.delete(device)
        db.session.commit()
        
        print(f"   ✓ 刪除 {points} 個數據點")
        print(f"   ✓ 刪除 {streams} 個數據流")
        print(f"   ✓ 刪除設備")
        print("\n✅ 設備清理完成！")

def show_statistics():
    """顯示資料庫統計"""
    app = create_app()
    with app.app_context():
        devices = Device.query.all()
        
        print("\n" + "="*60)
        print(" 📊 資料庫統計")
        print("="*60)
        
        print(f"\n總設備數: {len(devices)}")
        print(f"總 DataStream 數: {DataStream.query.count()}")
        print(f"總 DataPoint 數: {DataPoint.query.count()}")
        
        if devices:
            print("\n設備列表：")
            for device in devices:
                streams = DataStream.query.filter_by(device_mac=device.mac).count()
                points = DataPoint.query.filter_by(device_mac=device.mac).count()
                print(f"\n  📱 {device.mac}")
                print(f"     - IP: {device.ip or 'N/A'}")
                print(f"     - 晶片: {device.chip_type or 'N/A'}")
                print(f"     - DataStream: {streams}")
                print(f"     - DataPoint: {points}")
                print(f"     - 最後上線: {device.last_seen or 'N/A'}")
        else:
            print("\n✅ 資料庫是空的")
        
        print("\n" + "="*60)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'clear':
            clear_all_data()
        elif command == 'device' and len(sys.argv) > 2:
            mac = sys.argv[2]
            clear_specific_device(mac)
        elif command == 'stats':
            show_statistics()
        else:
            print("❌ 未知命令")
            print("\n使用方法：")
            print("  python clear_database.py clear         # 清除所有數據")
            print("  python clear_database.py device [MAC]  # 清除特定設備")
            print("  python clear_database.py stats         # 顯示統計")
    else:
        print("\n🗑️  資料庫清理工具")
        print("="*60)
        print("\n使用方法：")
        print("  python clear_database.py clear         # 清除所有數據")
        print("  python clear_database.py device [MAC]  # 清除特定設備")
        print("  python clear_database.py stats         # 顯示統計")
        print("\n範例：")
        print("  python clear_database.py clear")
        print("  python clear_database.py device AA:BB:CC:DD:EE:FF")
        print("  python clear_database.py stats")
        print()
