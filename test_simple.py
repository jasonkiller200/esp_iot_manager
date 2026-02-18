"""
簡單測試腳本 - 使用內建 urllib 模組測試 Blynk API
不需要安裝 requests
"""
import urllib.request
import urllib.parse
import time
import random

# 設定
BASE_URL = "http://localhost:5000"
DEVICE_TOKEN = "AA:BB:CC:DD:EE:FF"

def send_data(pin, value):
    """發送數據到 Blynk API"""
    url = f"{BASE_URL}/blynk/{DEVICE_TOKEN}/update/{pin}"
    params = urllib.parse.urlencode({'value': str(value)})
    full_url = f"{url}?{params}"
    
    try:
        with urllib.request.urlopen(full_url) as response:
            return response.status == 200
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False

def create_datastream(device_mac, pin, name, data_type, min_val, max_val, unit):
    """創建 DataStream 定義"""
    url = f"{BASE_URL}/blynk/admin/datastream"
    data = {
        'device_mac': device_mac,
        'pin': pin,
        'name': name,
        'data_type': data_type,
        'min': min_val,
        'max': max_val,
        'unit': unit
    }
    
    try:
        json_data = str(data).replace("'", '"').encode('utf-8')
        req = urllib.request.Request(url, data=json_data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            return response.status == 200
    except Exception as e:
        print(f"⚠️  創建失敗: {name} - {e}")
        return False

def main():
    print("\n" + "="*60)
    print(" 🌡️  ESP-IoT Manager - 簡易測試工具")
    print("="*60 + "\n")
    
    # 創建 DataStream 定義
    print("📝 創建 DataStream 定義...")
    datastreams = [
        (DEVICE_TOKEN, 'V0', 'Temperature', 'double', 0, 50, '°C'),
        (DEVICE_TOKEN, 'V1', 'Humidity', 'double', 0, 100, '%'),
        (DEVICE_TOKEN, 'V2', 'Pressure', 'double', 900, 1100, 'hPa'),
    ]
    
    for ds in datastreams:
        if create_datastream(*ds):
            print(f"   ✅ {ds[2]} ({ds[1]})")
        else:
            print(f"   ⚠️  {ds[2]} ({ds[1]}) - 可能已存在")
    
    print()
    print("🚀 開始發送測試數據")
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
            
            # 生成模擬數據
            value = random.uniform(sensor['min'], sensor['max'])
            
            # 發送數據
            if send_data(sensor['pin'], f"{value:.2f}"):
                print(f"✅ [{i+1:3d}] {sensor['name']:12s} ({sensor['pin']}): {value:7.2f}")
            else:
                print(f"❌ [{i+1:3d}] 發送失敗")
            
            # 隨機延遲
            time.sleep(random.uniform(0.5, 2))
            
    except KeyboardInterrupt:
        print("\n\n⏹️  測試已停止")
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")

if __name__ == '__main__':
    main()
