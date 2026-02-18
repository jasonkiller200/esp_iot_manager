# ESP-IoT Manager MQTT Library

完整的 ESP32/ESP8266 IoT 管理庫，支援 MQTT 即時通訊和 HTTP OTA 更新。

## 功能特色

- ✅ **MQTT 即時數據傳輸**（QoS 0/1/2）
- ✅ **HTTP OTA 無線更新**
- ✅ **Blynk Virtual Pin 相容**
- ✅ **自動重連機制**
- ✅ **雙向控制通訊**
- ✅ **ESP32 與 ESP8266 通用**

## 安裝方式

### 相依函式庫
請先安裝以下函式庫（透過 Arduino Library Manager）：
- `ArduinoJson` (v6.x)
- `PubSubClient` (v2.8+)

## 快速開始

```cpp
#include <ESP_IoT_Manager_MQTT.h>

// WiFi 和伺服器設定
ESP_IoT_Manager_MQTT iot("WIFI_SSID", "PASSWORD", "192.168.1.100");

void setup() {
  iot.begin("1.0.0");  // 初始化
  iot.setQoS(1);       // 設定 QoS = 1（保證送達）
}

void loop() {
  iot.loop();  // 必須呼叫
  
  // 發送數據（透過 MQTT）
  float temp = readTemperature();
  iot.sendData("V0", temp);  // 自動使用 MQTT 發送
  
  delay(10000);
}
```

## API 參考

### 初始化
```cpp
ESP_IoT_Manager_MQTT(ssid, password, serverIP, mqttPort=1883, httpPort=5000)
bool begin(version)
void setQoS(qos)  // 0=最多一次, 1=至少一次, 2=恰好一次
```

### 數據傳輸（MQTT）
```cpp
bool sendData(pin, value)  // 支援 float, int, const char*
```

### 即時控制
```cpp
void onControlMessage(callback)
// 回調格式: void callback(String pin, String value)
```

### OTA 更新（HTTP）
```cpp
void checkOTA()
```

### 狀態查詢
```cpp
bool isWiFiConnected()
bool isMQTTConnected()
String getMacAddress()
String getLocalIP()
```

## MQTT Topic 結構

### 數據上報
```
Topic: devices/{MAC}/data/{PIN}
Example: devices/AA:BB:CC:DD:EE:FF/data/V0
Payload: 25.5
```

### 接收控制指令
```
Topic: devices/{MAC}/control/{PIN}
Example: devices/AA:BB:CC:DD:EE:FF/control/V10
Payload: 1
```

### 設備狀態
```
Topic: devices/{MAC}/status
Payload: {"online":true,"ip":"192.168.1.100","version":"1.0.0"}
```

## 範例

### 基本數據上傳
```cpp
#include <ESP_IoT_Manager_MQTT.h>

ESP_IoT_Manager_MQTT iot("WIFI", "PASS", "192.168.1.100");

void setup() {
  iot.begin("1.0.0");
}

void loop() {
  iot.loop();
  
  iot.sendData("V0", analogRead(A0));  // 讀取類比輸入
  iot.sendData("V1", millis() / 1000); // 運行時間（秒）
  
  delay(5000);
}
```

### 雙向控制
```cpp
#include <ESP_IoT_Manager_MQTT.h>

ESP_IoT_Manager_MQTT iot("WIFI", "PASS", "192.168.1.100");
const int LED_PIN = 2;

void handleControl(String pin, String value) {
  if (pin == "V10") {
    digitalWrite(LED_PIN, value == "1" ? HIGH : LOW);
    iot.sendData("V10", value);  // 回報狀態
  }
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  iot.begin("1.0.0");
  iot.onControlMessage(handleControl);
}

void loop() {
  iot.loop();
}
```

### 關鍵數據（QoS 1）
```cpp
// 電表等關鍵數據使用 QoS 1
iot.setQoS(1);  // 保證送達

void loop() {
  iot.loop();
  
  float kWh = readPowerMeter();
  iot.sendData("V0", kWh);  // MQTT QoS 1，離線也會緩存
  
  delay(60000);
}
```

## 技術細節

### 自動重連
- WiFi 斷線自動重連（每 5 秒嘗試）
- MQTT 斷線自動重連（每 5 秒嘗試）
- 心跳機制保持連線（每 30 秒）

### QoS 說明
| QoS | 保證 | 用途 | 網路負載 |
|-----|------|------|---------|
| 0 | 最多一次 | 一般感測器 | 最低 |
| 1 | 至少一次 | 關鍵數據 | 中等 |
| 2 | 恰好一次 | 金融交易 | 最高 |

### 效能
- 延遲: < 100ms（區域網路）
- 支援設備數: 1000+（單一 Broker）
- 資料吞吐: ~1000 msgs/sec

## 故障排除

### MQTT 連線失敗
```cpp
Serial.println(iot.isMQTTConnected() ? "Connected" : "Disconnected");
```

### WiFi 無法連線
檢查 SSID 和密碼是否正確

### 數據未收到
確認 Mosquitto 服務運行中：
```bash
Get-Service mosquitto  # Windows
systemctl status mosquitto  # Linux
```

## 授權

MIT License
