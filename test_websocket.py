"""
測試 WebSocket 即時監控功能
模擬設備發送數據到 Blynk API，觀察 WebSocket 推送
"""
import requests
import time
import random

# 設定
BASE_URL = "http://localhost:5000"
DEVICE_TOKEN = "AA:BB:CC:DD:EE:FF"  # 測試設備 MAC

def test_blynk_api():
    """測試 Blynk API 並觀察數據更新"""
    
    print("🚀 開始測試 WebSocket 即時監控功能")
    print(f"📡 設備 MAC: {DEVICE_TOKEN}")
    print(f"🌐 請在瀏覽器打開: {BASE_URL}/dashboard")
    print(f"📊 設備詳情頁: {BASE_URL}/dashboard/device/{DEVICE_TOKEN}")
    print("\n" + "="*60 + "\n")
    
    # 模擬感測器數據
    sensors = [
        {'pin': 'V0', 'name': 'Temperature', 'min': 20, 'max': 30},
        {'pin': 'V1', 'name': 'Humidity', 'min': 40, 'max': 80},
        {'pin': 'V2', 'name': 'Pressure', 'min': 990, 'max': 1020},
    ]
    
    try:
        for i in range(100):
            # 隨機選擇一個感測器
            sensor = random.choice(sensors)
            
            # 生成模擬數據（帶點變化）
            value = random.uniform(sensor['min'], sensor['max'])
            
            # 發送到 Blynk API
            url = f"{BASE_URL}/blynk/{DEVICE_TOKEN}/update/{sensor['pin']}"
            params = {'value': f"{value:.2f}"}
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                print(f"✅ [{i+1:3d}] {sensor['name']:12s} ({sensor['pin']}): {value:7.2f}")
            else:
                print(f"❌ Error: {response.status_code}")
            
            # 隨機延遲 0.5-2 秒
            time.sleep(random.uniform(0.5, 2))
            
    except KeyboardInterrupt:
        print("\n\n⏹️  測試已停止")
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")

def create_datastreams():
    """初始化 DataStream 定義"""
    datastreams = [
        {
            'device_mac': DEVICE_TOKEN,
            'pin': 'V0',
            'name': 'Temperature',
            'data_type': 'double',
            'min': 0,
            'max': 50,
            'unit': '°C'
        },
        {
            'device_mac': DEVICE_TOKEN,
            'pin': 'V1',
            'name': 'Humidity',
            'data_type': 'double',
            'min': 0,
            'max': 100,
            'unit': '%'
        },
        {
            'device_mac': DEVICE_TOKEN,
            'pin': 'V2',
            'name': 'Pressure',
            'data_type': 'double',
            'min': 900,
            'max': 1100,
            'unit': 'hPa'
        },
    ]
    
    print("📝 創建 DataStream 定義...")
    for ds in datastreams:
        url = f"{BASE_URL}/blynk/admin/datastream"
        response = requests.post(url, json=ds)
        if response.status_code == 200:
            print(f"   ✅ {ds['name']} ({ds['pin']})")
        else:
            print(f"   ⚠️  {ds['name']} - {response.status_code}")
    
    print()

if __name__ == '__main__':
    print("\n" + "="*60)
    print(" 🌡️  ESP-IoT Manager - WebSocket 即時監控測試")
    print("="*60 + "\n")
    
    # 先創建 DataStream 定義
    create_datastreams()
    
    # 執行測試
    test_blynk_api()
