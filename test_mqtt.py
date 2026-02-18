"""
快速測試 MQTT 整合是否正常
"""
from app import create_app
from app.mqtt_manager import mqtt_manager
import time

app = create_app()

with app.app_context():
    print("=" * 50)
    print("🚀 ESP-IoT Manager - MQTT 測試")
    print("=" * 50)
    
    # 等待MQTT連線
    print("\n⏳ 等待 MQTT 連線...")
    time.sleep(2)
    
    if mqtt_manager.connected:
        print("✅ MQTT Broker 已連線！")
        print(f"📡 已訂閱主題: devices/+/data/+")
        print(f"📡 已訂閱主題: devices/+/status")
        print("\n💡 測試指令：")
        print('cd "C:\\Program Files\\mosquitto"')
        print('.\\mosquitto_pub.exe -h localhost -t devices/TEST001/data/V0 -m "25.5"')
        print("\n🎯 Flask 伺服器運行中...")
        print(f"🌐 http://127.0.0.1:5000")
        print(f"🌐 http://192.168.50.170:5000")
        print("\n按 Ctrl+C 停止")
        
        # 保持運行
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    else:
        print("❌ MQTT Broker 連線失敗")
        print("請確認:")
        print("1. Mosquitto 服務是否運行: Get-Service mosquitto")
        print("2. Port 1883 是否開放: netstat -ano | findstr :1883")
