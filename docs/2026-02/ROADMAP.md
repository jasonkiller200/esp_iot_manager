# ESP-IoT Manager - 完整實作計畫（20+ 設備）

## 📅 開發時程（建議 2-3 週）

### Week 1: MQTT 基礎建設
- [x] Day 1-2: 安裝 Mosquitto + 測試
- [ ] Day 3-4: Flask MQTT 整合
- [ ] Day 5-6: 建立數據模型（DataStream, DataPoint）
- [ ] Day 7: 測試 MQTT 數據收集

### Week 2: Blynk API + Arduino Library
- [ ] Day 8-9: 實作 Blynk 相容 API
- [ ] Day 10-12: 更新 Arduino Library 支援 MQTT
- [ ] Day 13-14: 測試多設備連線（模擬 5 台）

### Week 3: 進階功能 + 上線
- [ ] Day 15-16: WebSocket 即時介面
- [ ] Day 17-18: 數據視覺化（Chart.js）
- [ ] Day 19-20: 壓力測試（20 台設備）
- [ ] Day 21: 部署上線

---

## 🎯 立即行動清單

### ✅ 今日任務（2 小時）

#### 1. 安裝 Mosquitto（20 分鐘）
```powershell
# 下載安裝
https://mosquitto.org/files/binary/win64/mosquitto-2.0.18-install-windows-x64.exe

# 編輯設定檔
notepad "C:\Program Files\mosquitto\mosquitto.conf"
# 加入：
# listener 1883
# allow_anonymous true

# 啟動服務
net start mosquitto
```

#### 2. 測試 MQTT（10 分鐘）
```powershell
# 視窗 1
cd "C:\Program Files\mosquitto"
.\mosquitto_sub.exe -h localhost -t test -v

# 視窗 2
.\mosquitto_pub.exe -h localhost -t test -m "Hello"
```

#### 3. 安裝 Python 套件（5 分鐘）
```powershell
cd D:\ai_develop\esp_iot_manager
.\venv\Scripts\activate
pip install paho-mqtt
```

#### 4. 建立數據模型（30 分鐘）
```python
# 已建立檔案：
# - app/models/datastream.py
# - app/mqtt_manager.py
# - config.py (已更新)

# 需要執行資料庫遷移
flask db migrate -m "Add MQTT data models"
flask db upgrade
```

#### 5. 啟動 Flask 測試（10 分鐘）
```powershell
python run.py
# 檢查 Console 是否顯示 "✅ Connected to MQTT Broker"
```

#### 6. ESP 測試（45 分鐘）
使用現有的 esp8266_test.ino 測試 HTTP 是否正常

---

## 🔧 技術架構總覽（最終版本）

```
┌────────────────────────────────────────────────┐
│ ESP32/ESP8266 設備（20+ 台）                   │
│                                                │
│ 使用 ESP_IoT_Manager Library:                 │
│  ├─ MQTT: iot.sendData() → 即時數據           │
│  ├─ HTTP: iot.checkOTA() → 韌體更新           │
│  └─ WebSocket: onControlMessage() → 控制      │
└─────────┬──────────────────────────────────────┘
          │
          ↓ MQTT (Port 1883) + HTTP (Port 5000)
┌────────────────────────────────────────────────┐
│ 伺服器層                                       │
│                                                │
│ Mosquitto Broker (Port 1883)                  │
│  ├─ QoS 1 保證數據送達                        │
│  ├─ 離線設備消息緩存                          │
│  └─ 支援 1000+ 並發連線                       │
│                                                │
│ Flask 後端 (Port 5000)                        │
│  ├─ MQTT Client: 訂閱設備數據                │
│  ├─ /api/*: 設備管理、OTA                    │
│  ├─ /blynk/*: Blynk 相容 API                 │
│  └─ WebSocket: Web 即時更新                  │
└─────────┬──────────────────────────────────────┘
          │
          ↓
┌────────────────────────────────────────────────┐
│ SQLite 資料庫                                  │
│  ├─ devices: 設備列表、狀態                   │
│  ├─ datastreams: Virtual Pin 定義             │
│  ├─ datapoints: 時間序列數據                  │
│  └─ firmware: 韌體版本管理                    │
└────────────────────────────────────────────────┘
          │
          ↓
┌────────────────────────────────────────────────┐
│ Web 介面 (Vue.js / React 可選)                │
│  ├─ 設備列表與狀態                            │
│  ├─ 即時數據圖表 (Chart.js)                  │
│  ├─ 控制面板（開關、滑桿）                    │
│  └─ OTA 更新管理                              │
└────────────────────────────────────────────────┘
```

---

## 📊 各功能使用的技術

| 功能 | ESP → 伺服器 | 伺服器 → ESP | 協議 | QoS |
|------|-------------|-------------|------|-----|
| 感測器數據 | ✅ | - | MQTT | 1 |
| 設備狀態 | ✅ | - | MQTT | 0 |
| LED 控制 | - | ✅ | MQTT | 1 |
| 繼電器控制 | - | ✅ | MQTT | 1 |
| OTA 更新 | ✅ | ✅ | HTTP | - |
| 歷史查詢 | - | ✅ | HTTP REST | - |
| 設備註冊 | ✅ | - | HTTP | - |

---

## 🔐 MQTT Topic 命名規範

### 數據上報（ESP → 伺服器）
```
devices/{MAC}/data/{PIN}
範例：devices/AA:BB:CC:DD:EE:FF/data/V0
Payload: 25.5
```

### 控制指令（伺服器 → ESP）
```
devices/{MAC}/control/{PIN}
範例：devices/AA:BB:CC:DD:EE:FF/control/V10
Payload: 1
```

### 設備狀態
```
devices/{MAC}/status
Payload: {"online": true, "ip": "192.168.1.100", "rssi": -45}
```

### 廣播指令（所有設備）
```
devices/broadcast/control
Payload: {"action": "reboot"}
```

---

## 💾 數據保留策略（避免資料庫爆炸）

### 原始數據保留
- 最近 7 天：保留所有原始數據（每秒/每分鐘）
- 8-30 天：每 5 分鐘聚合平均
- 31-365 天：每小時聚合平均
- 超過 1 年：每日聚合平均

### 實作方式
```python
# 定期執行的清理腳本
def aggregate_old_data():
    # 將 7 天前的數據聚合為 5 分鐘平均
    # 將 30 天前的數據聚合為 1 小時平均
    # 刪除 1 年前的原始數據
```

---

## 📈 效能優化建議

### 資料庫索引
```sql
CREATE INDEX idx_datapoint_mac_pin ON datapoint(device_mac, pin);
CREATE INDEX idx_datapoint_timestamp ON datapoint(timestamp);
CREATE INDEX idx_datapoint_mac_time ON datapoint(device_mac, timestamp);
```

### MQTT QoS 選擇
- 一般感測器：QoS 0（允許偶爾遺失）
- 關鍵數據（電表）：QoS 1（保證送達）
- 控制指令：QoS 1（確保執行）

### 記憶體管理
- ESP 端限制緩存數量：100 筆
- Mosquitto 設定最大消息大小：1MB
- Flask 使用 Redis 緩存熱門查詢

---

## 🚨 監控與告警

### 建議監控項目
1. MQTT Broker 連線數
2. 每秒訊息數量（TPS）
3. 資料庫大小增長速度
4. 離線設備數量
5. API 回應時間

### 告警條件
- 設備超過 5 分鐘未回報 → 發送通知
- 資料庫超過 10GB → 執行清理
- MQTT 連線數 > 900 → 擴展 Broker

---

## 📚 相關文檔

- [MQTT_SETUP.md](MQTT_SETUP.md) - Mosquitto 安裝指南
- [ARCHITECTURE.md](ARCHITECTURE.md) - 整體架構說明
- [Arduino Library README](arduino_library/ESP_IoT_Manager/README.md) - ESP 端使用

---

## ✅ 驗收標準

### Phase 1: MQTT 基礎（本週）
- [ ] Mosquitto 正常運行
- [ ] Flask 可接收 MQTT 訊息
- [ ] 數據正確儲存到資料庫
- [ ] 可從 Web 介面查看即時數據

### Phase 2: 完整功能（第 2 週）
- [ ] 20 台設備模擬測試
- [ ] 數據無遺失
- [ ] 延遲 < 1 秒
- [ ] OTA 更新成功率 > 95%

### Phase 3: 生產就緒（第 3 週）
- [ ] 壓力測試：100 台設備
- [ ] 24 小時穩定運行
- [ ] 資料庫自動清理
- [ ] 監控與告警系統

---

## 🎓 學習資源

- MQTT 協議入門: https://mqtt.org/
- Mosquitto 文檔: https://mosquitto.org/man/
- Flask-MQTT: https://flask-mqtt.readthedocs.io/
- Blynk API 參考: https://docs.blynk.io/
