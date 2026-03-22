# ESP-IoT Manager 架構說明

## 方案對比

### 目前方案（HTTP Only）
```
ESP32/ESP8266
    ↓ HTTP POST（每 30 秒）
Flask (Port 5000)
    ↓
SQLite 資料庫
```

**優點：** 簡單
**缺點：** 
- 離線會遺失數據
- 無法即時控制設備
- 高延遲（30秒）


### 加入 MQTT 後
```
ESP32/ESP8266
    ↓ MQTT Publish（即時）
Mosquitto Broker (Port 1883)
    ├─→ Flask 訂閱數據
    │   ↓
    │   SQLite 資料庫
    │
    └─→ Web 介面即時顯示
```

**優點：**
- ✅ 離線數據自動緩存
- ✅ 即時雙向通訊
- ✅ 低延遲（毫秒級）
- ✅ 支援多設備同時連線

**缺點：**
- 需要多運行一個服務（Mosquitto）


## 資源需求

| 服務 | Port | 記憶體 | CPU |
|------|------|--------|-----|
| Flask | 5000 | ~50MB | 低 |
| Mosquitto | 1883 | ~5MB | 極低 |
| 總計 | - | ~55MB | 低 |

**結論：** 一台普通電腦完全足夠運行


## 安裝步驟（Windows 11）

### 1. 安裝 Mosquitto
```powershell
# 下載安裝檔
https://mosquitto.org/files/binary/win64/mosquitto-2.0.18-install-windows-x64.exe

# 或使用 Chocolatey
choco install mosquitto
```

### 2. 設定 Mosquitto
編輯 `C:\Program Files\mosquitto\mosquitto.conf`：
```conf
listener 1883
allow_anonymous true
```

### 3. 啟動服務
```powershell
# 方法 1: Windows 服務
net start mosquitto

# 方法 2: 手動啟動（測試用）
cd "C:\Program Files\mosquitto"
mosquitto -v -c mosquitto.conf
```

### 4. 測試連線
```powershell
# 訂閱測試主題
mosquitto_sub -h localhost -t test

# 另一個 PowerShell 視窗發送訊息
mosquitto_pub -h localhost -t test -m "Hello"
```


## ESP 端代碼變化

### 原本（HTTP）
```cpp
iot.sendData("V0", 25.5);  // 30 秒一次
```

### 加入 MQTT
```cpp
mqtt.publish("device/AA:BB:CC/V0", "25.5");  // 即時發送
```


## Flask 端整合

### 安裝 Python 套件
```bash
pip install paho-mqtt
```

### 訂閱 MQTT 數據
```python
import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    # 收到 ESP 的數據
    topic = msg.topic  # "device/AA:BB:CC/V0"
    value = msg.payload.decode()
    
    # 儲存到資料庫
    save_to_database(topic, value)

client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883)
client.subscribe("device/#")  # 訂閱所有設備
client.loop_start()
```


## 是否需要 MQTT？

### 保持 HTTP 即可（推薦新手）
- ✅ 只需數據收集
- ✅ 可接受 30 秒延遲
- ✅ 少於 10 台設備
- ✅ 想保持簡單

### 建議加入 MQTT
- ✅ 需要即時控制（開關燈）
- ✅ 需要低延遲（< 1 秒）
- ✅ 關鍵數據不能遺失（電表）
- ✅ 超過 20 台設備


## 混合方案（最佳實踐）

```
ESP 設備
├─ MQTT：即時數據、控制指令
└─ HTTP：韌體更新（OTA）、心跳

Flask 後端
├─ MQTT Client：訂閱即時數據
├─ REST API：歷史數據查詢
└─ WebSocket：Web 介面即時更新
```

這樣可以：
- 即時數據用 MQTT（快速、可靠）
- OTA 更新用 HTTP（檔案傳輸方便）
- 歷史查詢用 REST API（標準化）
