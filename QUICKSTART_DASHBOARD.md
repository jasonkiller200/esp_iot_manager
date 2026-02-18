# 快速開始 - Web 即時監控

## 1. 啟動應用

```bash
python run.py
```

## 2. 開啟瀏覽器

### 主儀表板
```
http://localhost:5000/dashboard
```

### 傳統管理介面
```
http://localhost:5000/
```

## 3. 測試即時監控

在新終端執行：

```bash
python test_websocket.py
```

然後在瀏覽器中觀察：
- ✅ 數據即時更新（無需刷新）
- ✅ 圖表自動繪製
- ✅ WebSocket 連接狀態

## 功能演示

### 儀表板功能
- 📊 設備統計卡片（總數/線上/離線）
- 📝 設備列表（MAC、IP、版本、狀態）
- 🔄 自動刷新（30秒）
- 🔌 WebSocket 連接指示器

### 設備詳情頁
- 📈 即時數據指標卡片
- 📉 Chart.js 即時趨勢圖
- 📊 統計分析（最小/最大/平均值）
- ⏱️ 可選時間範圍（1h/6h/24h/7d）
- 🔄 自動更新（10秒）
- 🔴 WebSocket 即時推送

## 設備整合

### 透過 Blynk API
```bash
# 發送數據
curl "http://localhost:5000/blynk/AA:BB:CC:DD:EE:FF/update/V0?value=25.5"
```

### 透過 MQTT
```bash
# 發布數據
mosquitto_pub -h localhost -t "devices/AA:BB:CC:DD:EE:FF/data/V0" -m "25.5"
```

## Arduino 範例

```cpp
#include <ESP_IoT_Manager_MQTT.h>

ESP_IoT_Manager iot("YOUR_WIFI_SSID", "YOUR_WIFI_PASSWORD");

void setup() {
  Serial.begin(115200);
  
  // 連接到伺服器
  iot.setServerURL("http://192.168.1.100:5000");
  iot.setMQTTServer("192.168.1.100", 1883);
  iot.begin();
}

void loop() {
  iot.loop();
  
  // 讀取感測器
  float temperature = readTemperature();
  float humidity = readHumidity();
  
  // 發送數據（會自動透過 WebSocket 推送到前端）
  iot.sendData("V0", temperature);
  iot.sendData("V1", humidity);
  
  delay(5000);
}
```

## 更多資訊

詳細文檔請參考：
- `DASHBOARD_README.md` - 完整功能說明
- `MQTT_SETUP.md` - MQTT 設置指南
- `ARCHITECTURE.md` - 系統架構文檔
