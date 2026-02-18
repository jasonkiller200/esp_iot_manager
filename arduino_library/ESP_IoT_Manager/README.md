# ESP-IoT Manager Arduino Library

適用於 ESP32 和 ESP8266 的 IoT 設備管理函式庫，提供類似 Blynk 的簡單 API。

## 功能特色

- ✅ **自動 WiFi 連線管理**
- ✅ **Virtual Pin 數據傳輸**（Blynk 相容）
- ✅ **WebSocket 即時雙向通訊**
- ✅ **OTA 無線更新**
- ✅ **自動心跳保持連線**
- ✅ **ESP32 與 ESP8266 通用**

## 安裝方式

### 方法 1: Arduino IDE 手動安裝
1. 下載此專案
2. 將 `ESP_IoT_Manager` 資料夾複製到 Arduino libraries 目錄：
   - Windows: `Documents\Arduino\libraries\`
   - macOS: `~/Documents/Arduino/libraries/`
   - Linux: `~/Arduino/libraries/`
3. 重啟 Arduino IDE

### 方法 2: 從壓縮檔安裝
1. 壓縮 `ESP_IoT_Manager` 資料夾為 ZIP
2. Arduino IDE → 草稿碼 → 匯入程式庫 → 加入 .ZIP 程式庫

## 相依函式庫

請先安裝以下函式庫（透過 Arduino Library Manager）：
- `ArduinoJson` (v6.x)
- `WebSockets` by Markus Sattler

## 快速開始

### 基本使用範例

```cpp
#include <ESP_IoT_Manager.h>

ESP_IoT_Manager iot("WIFI_SSID", "PASSWORD", "192.168.1.100");

void setup() {
  iot.begin("1.0.0");  // 初始化，參數為韌體版本
}

void loop() {
  iot.loop();  // 必須呼叫
  
  // 發送數據到 Virtual Pin
  float temp = readTemperature();
  iot.sendData("V0", temp);
  
  delay(10000);
}
```

### 即時控制範例

```cpp
#include <ESP_IoT_Manager.h>

ESP_IoT_Manager iot("WIFI_SSID", "PASSWORD", "192.168.1.100");

const int LED_PIN = 2;

// 接收控制指令的回調函式
void handleControl(String pin, String value) {
  if (pin == "V10") {
    digitalWrite(LED_PIN, value == "1" ? HIGH : LOW);
  }
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  iot.begin("1.0.0");
  iot.onControlMessage(handleControl);  // 註冊回調
}

void loop() {
  iot.loop();
}
```

## API 參考

### 初始化

```cpp
ESP_IoT_Manager(ssid, password, serverIP, serverPort)
bool begin(version)  // 連接 WiFi 並初始化
```

### 數據傳輸

```cpp
bool sendData(pin, value)           // 發送單一數據
bool sendMultiple(pins[], values[], count)  // 批量發送
```

支援的數據類型：`float`, `int`, `const char*`

### 即時控制

```cpp
void onControlMessage(callback)  // 註冊接收指令的回調函式
// 回調格式: void callback(String pin, String value)
```

### OTA 更新

```cpp
void checkOTA()  // 手動觸發 OTA 檢查
```

### 工具函式

```cpp
bool isConnected()      // 檢查 WiFi 連線狀態
String getMacAddress()  // 取得 MAC 位址
String getLocalIP()     // 取得 IP 位址
```

## Virtual Pin 對應

與 Blynk 相同，使用 `V0` ~ `V255` 作為虛擬腳位：

| Pin | 用途範例 |
|-----|---------|
| V0-V9 | 感測器數據（溫度、濕度等） |
| V10-V19 | 控制輸出（LED、繼電器） |
| V20-V29 | 狀態訊息 |

## 伺服器 API 端點

Library 會自動呼叫以下 API：

- `POST /api/update_status` - 心跳與狀態回報
- `GET /blynk/{mac}/update/{pin}?value=xxx` - 發送數據
- `WebSocket /ws` - 即時雙向通訊

## 範例專案

- `BasicUsage.ino` - 基本數據上傳
- `RemoteControl.ino` - 即時控制 LED

## 授權

MIT License

## 作者

Your Name - your.email@example.com
