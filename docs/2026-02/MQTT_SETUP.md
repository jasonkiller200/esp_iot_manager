# ESP-IoT Manager - MQTT 快速安裝指南

## 🚀 步驟 1: 安裝 Mosquitto MQTT Broker（5 分鐘）

### Windows 11 安裝方式

#### 方法 1: 官方安裝檔（推薦）
1. 下載安裝檔：
   https://mosquitto.org/files/binary/win64/mosquitto-2.0.18-install-windows-x64.exe

2. 執行安裝檔，全部選預設值

3. 安裝完成後，編輯設定檔：
   - 路徑：`C:\Program Files\mosquitto\mosquitto.conf`
   - 在檔案最後加入：
   ```
   listener 1883
   allow_anonymous true
   ```

4. 啟動服務：
   ```powershell
   net start mosquitto
   ```

#### 方法 2: 手動下載（免安裝）
1. 下載壓縮檔：
   https://mosquitto.org/files/binary/win64/mosquitto-2.0.18-win64.zip

2. 解壓縮到 `D:\mosquitto`

3. 建立設定檔 `D:\mosquitto\mosquitto.conf`：
   ```
   listener 1883
   allow_anonymous true
   persistence true
   persistence_location D:/mosquitto/data/
   log_dest file D:/mosquitto/mosquitto.log
   ```

4. 啟動：
   ```powershell
   cd D:\mosquitto
   mosquitto.exe -v -c mosquitto.conf
   ```

---

## ✅ 步驟 2: 測試 MQTT Broker

### 打開兩個 PowerShell 視窗

**視窗 1（訂閱者）：**
```powershell
cd "C:\Program Files\mosquitto"
.\mosquitto_sub.exe -h localhost -t test/topic -v
```

**視窗 2（發布者）：**
```powershell
cd "C:\Program Files\mosquitto"
.\mosquitto_pub.exe -h localhost -t test/topic -m "Hello MQTT"
```

如果視窗 1 顯示 `test/topic Hello MQTT`，代表成功！

---

## 🔧 步驟 3: 安裝 Python MQTT 套件

```powershell
cd D:\ai_develop\esp_iot_manager
.\venv\Scripts\activate
pip install paho-mqtt
```

---

## 📊 MQTT 主題結構設計

### 建議的 Topic 命名規則

```
devices/{mac_address}/data/{pin}        # 數據上報
devices/{mac_address}/control/{pin}     # 控制指令
devices/{mac_address}/status            # 設備狀態
devices/{mac_address}/log               # 日誌訊息
```

### 範例：

```
# ESP 發送溫度數據
Topic: devices/AA:BB:CC:DD:EE:FF/data/V0
Payload: 25.5

# 伺服器控制 LED
Topic: devices/AA:BB:CC:DD:EE:FF/control/V10
Payload: 1

# 設備上線通知
Topic: devices/AA:BB:CC:DD:EE:FF/status
Payload: {"online": true, "ip": "192.168.1.100"}
```

---

## 🎯 建議的完整架構（20+ 設備）

```
┌─────────────────────────────────────────────┐
│ 20+ ESP32/ESP8266 設備                      │
│ ├─ MQTT: 即時數據 (QoS 1)                  │
│ │   └─ 每秒可發送數據                      │
│ └─ HTTP: OTA 更新、初次註冊               │
└──────────┬──────────────────────────────────┘
           │
           ↓ Port 1883
┌─────────────────────────────────────────────┐
│ Mosquitto MQTT Broker                       │
│ ├─ 離線消息緩存 (QoS 1/2)                  │
│ ├─ 支援 1000+ 設備                          │
│ └─ 記憶體使用: ~10MB                        │
└──────────┬──────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────────┐
│ Flask 後端 (Port 5000)                      │
│ ├─ MQTT Client: 訂閱所有設備數據           │
│ ├─ HTTP API: 歷史查詢、OTA                 │
│ └─ WebSocket: Web 介面即時更新             │
└──────────┬──────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────────┐
│ SQLite 資料庫                               │
│ ├─ devices: 設備列表                       │
│ ├─ datastreams: Virtual Pin 定義           │
│ └─ datapoints: 時間序列數據                │
└─────────────────────────────────────────────┘
```

---

## 📝 各協議用途分配

| 功能 | 使用協議 | 原因 |
|------|---------|------|
| **感測器數據上報** | MQTT | 即時、可靠、低延遲 |
| **設備控制** | MQTT | 雙向即時通訊 |
| **韌體更新(OTA)** | HTTP | 大檔案傳輸方便 |
| **設備註冊** | HTTP | 一次性操作 |
| **歷史數據查詢** | HTTP REST | 標準化、Blynk 相容 |
| **Web 介面更新** | WebSocket | 瀏覽器即時顯示 |

---

## ⚡ 效能對比（20 台設備）

### HTTP 方案
```
20 設備 × 每 30 秒 = 40 請求/分
- 延遲: 30 秒
- 離線風險: 高
- 並發壓力: 中
```

### MQTT 方案
```
20 設備持續連線
- 延遲: < 100ms
- 離線風險: 無（Broker 緩存）
- 並發壓力: 低（持久連線）
```

### 100 台設備擴展
```
HTTP: 200 請求/分 ⚠️ 開始吃力
MQTT: 輕鬆應付 ✅
```

---

## 🔐 安全性考量（生產環境）

### 開發階段（當前）
```conf
allow_anonymous true  # 允許匿名連線
```

### 生產環境（未來）
```conf
allow_anonymous false
password_file /etc/mosquitto/passwd

# 建立密碼檔
mosquitto_passwd -c passwd username
```

ESP 端需要帳號密碼：
```cpp
mqtt.setCredentials("username", "password");
```

---

## 📦 下一步計畫

1. ✅ 安裝 Mosquitto（本檔案）
2. ⏳ 建立 Flask MQTT 整合
3. ⏳ 更新 Arduino Library 支援 MQTT
4. ⏳ 建立 Blynk 相容 API
5. ⏳ 測試多設備連線

---

## 🆘 常見問題

### Q: Mosquitto 服務無法啟動？
```powershell
# 檢查 Port 是否被佔用
netstat -ano | findstr :1883

# 查看服務狀態
Get-Service mosquitto
```

### Q: ESP 連線失敗？
```cpp
// 檢查 IP 是否正確
mqtt.setServer("192.168.1.100", 1883);

// 啟用 Debug
mqtt.setDebugOutput(true);
```

### Q: 多台設備是否會衝突？
不會！每台設備使用不同的 MAC 作為識別：
```
devices/AA:BB:CC:DD:EE:01/data/V0
devices/AA:BB:CC:DD:EE:02/data/V0
```

---

## 📚 參考資料

- Mosquitto 官方文檔: https://mosquitto.org/documentation/
- MQTT 協議說明: https://mqtt.org/
- Paho MQTT Python: https://pypi.org/project/paho-mqtt/
