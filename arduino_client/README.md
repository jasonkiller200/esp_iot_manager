# Arduino 測試程式使用說明

本目錄包含 NodeMCU (ESP8266) 和 ESP32 的測試程式，用於測試 IoT Manager 的即時監控功能。

## 📁 目錄結構

```
arduino_client/
├── NodeMCU_Test/
│   └── NodeMCU_Test.ino     # ESP8266 測試程式
└── ESP32_Test/
    └── ESP32_Test.ino        # ESP32 測試程式
```

## 🔧 硬體要求

### NodeMCU (ESP8266)
- 板子：NodeMCU 1.0 (ESP-12E Module)
- 晶片：ESP8266
- 虛擬腳位：V0-V4

### ESP32
- 板子：ESP32 Dev Module
- 晶片：ESP32
- 虛擬腳位：V5-V9

## 📊 模擬感測器

### NodeMCU (ESP8266) - V0-V4
| Pin | 名稱 | 範圍 | 單位 |
|-----|------|------|------|
| V0  | Temperature (溫度) | 15-35 | °C |
| V1  | Humidity (濕度) | 30-90 | % |
| V2  | Light (光線) | 0-1000 | Lux |
| V3  | Soil Moisture (土壤濕度) | 0-100 | % |
| V4  | Battery (電池) | 3.0-4.2 | V |

### ESP32 - V5-V9
| Pin | 名稱 | 範圍 | 單位 |
|-----|------|------|------|
| V5  | CPU Temperature (CPU溫度) | 30-80 | °C |
| V6  | Pressure (氣壓) | 980-1040 | hPa |
| V7  | Altitude (海拔) | 0-500 | m |
| V8  | CO2 | 400-2000 | ppm |
| V9  | RSSI (WiFi信號) | -90~-30 | dBm |

## 🚀 使用步驟

### 1. 準備環境

**安裝 Arduino IDE：**
- 下載：https://www.arduino.cc/en/software
- 版本：1.8.x 或 2.x

**安裝開發板支援：**

**ESP8266：**
```
工具 → 開發板 → 開發板管理員
搜尋：esp8266
安裝：ESP8266 Community (by ESP8266 Community)
```

**ESP32：**
```
工具 → 開發板 → 開發板管理員
搜尋：esp32
安裝：esp32 (by Espressif Systems)
```

### 2. 修改程式碼

**開啟程式檔案：**
- NodeMCU: `NodeMCU_Test/NodeMCU_Test.ino`
- ESP32: `ESP32_Test/ESP32_Test.ino`

**修改設定（在程式開頭）：**

```cpp
// WiFi 設定
const char* ssid = "YOUR_WIFI_SSID";          // 修改為你的 WiFi 名稱
const char* password = "YOUR_WIFI_PASSWORD";  // 修改為你的 WiFi 密碼

// 伺服器設定
const char* serverUrl = "http://192.168.1.100:5000";  // 修改為你的伺服器 IP
```

**重要：** 
- `serverUrl` 需要填寫運行 IoT Manager 的電腦 IP
- 確保 ESP8266/ESP32 和電腦在同一個網路

### 3. 上傳程式

**NodeMCU (ESP8266)：**
1. 連接 NodeMCU 到電腦 USB
2. 選擇板子：`工具 → 開發板 → ESP8266 Boards → NodeMCU 1.0`
3. 選擇 Port：`工具 → 序列埠 → COM?`
4. 上傳程式：點擊 `上傳` 按鈕

**ESP32：**
1. 連接 ESP32 到電腦 USB
2. 選擇板子：`工具 → 開發板 → ESP32 Arduino → ESP32 Dev Module`
3. 選擇 Port：`工具 → 序列埠 → COM?`
4. 上傳程式：點擊 `上傳` 按鈕

### 4. 查看運行結果

**開啟序列埠監控視窗：**
```
工具 → 序列埠監控視窗
設定鮑率：115200
```

**預期輸出：**

```
=====================================
  ESP8266 IoT Manager 測試程式
  裝置類型: NodeMCU
=====================================
MAC 地址: AA:BB:CC:DD:EE:FF

📡 連接 WiFi: YourWiFi
......
✅ WiFi 連接成功！
   IP 地址: 192.168.1.101
   信號強度: -45 dBm

📝 創建 DataStream 定義...
   ✅ Temperature (V0)
   ✅ Humidity (V1)
   ✅ Light (V2)
   ✅ Soil Moisture (V3)
   ✅ Battery (V4)

✅ 初始化完成！
開始發送模擬數據...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 [5s] ESP8266 發送數據：
   ✅ Temperature: 25.34 °C
   ✅ Humidity: 65.72 %
   ✅ Light: 456.89 Lux
   ✅ Soil Moisture: 78.23 %
   ✅ Battery: 3.85 V
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ 成功: 5/5 | 耗時: 312ms
```

## 🌐 查看即時監控

### 方法 1：主儀表板
```
http://localhost:5000/dashboard
```
- 可以看到兩個設備（NodeMCU 和 ESP32）
- 顯示線上狀態
- 顯示最後更新時間

### 方法 2：設備詳情頁

**NodeMCU：**
```
http://localhost:5000/dashboard/device/[NodeMCU_MAC]
```

**ESP32：**
```
http://localhost:5000/dashboard/device/[ESP32_MAC]
```

**功能：**
- ✅ 即時數據卡片（5 個虛擬腳位）
- ✅ 即時趨勢圖表（Chart.js）
- ✅ 統計分析（最小/最大/平均值）
- ✅ WebSocket 自動更新（無需刷新）

## 🔍 故障排除

### WiFi 連接失敗
1. 檢查 SSID 和密碼是否正確
2. 確認 WiFi 是 2.4GHz（ESP8266 不支援 5GHz）
3. 檢查 WiFi 信號強度

### 數據發送失敗
1. 檢查伺服器 IP 是否正確
2. 確認 IoT Manager 應用正在運行
3. 確認防火牆沒有阻擋 5000 端口
4. Ping 測試伺服器：`ping 192.168.1.100`

### 序列埠找不到
1. 安裝 USB 驅動（CP2102 或 CH340）
2. 重新插拔 USB 線
3. 檢查裝置管理員

### HTTP 錯誤
- HTTP 200：成功
- HTTP 404：找不到端點（檢查 serverUrl）
- HTTP 500：伺服器錯誤（檢查伺服器日誌）
- HTTP -1：連接失敗（檢查網路）

## 📝 自訂感測器

如果要修改感測器定義，編輯程式中的 `sensors[]` 陣列：

```cpp
Sensor sensors[] = {
  {"V0", "新感測器名稱", 最小值, 最大值, "單位"},
  // ... 更多感測器
};
```

**注意：**
- NodeMCU 和 ESP32 使用不同的虛擬腳位（避免衝突）
- 修改後需要重新上傳程式

## 🎯 測試場景

### 場景 1：單一設備測試
1. 上傳 NodeMCU 程式
2. 開啟儀表板觀察數據

### 場景 2：雙設備測試
1. 同時上傳 NodeMCU 和 ESP32 程式
2. 兩個設備同時發送數據
3. 儀表板顯示兩個設備
4. 每個設備各有 5 個數據流

### 場景 3：壓力測試
1. 修改 `sendInterval` 為更短間隔（如 1000ms）
2. 觀察系統負載和響應時間

## 💡 進階設定

### 修改發送間隔
```cpp
const unsigned long sendInterval = 3000;  // 改為 3 秒
```

### 添加更多虛擬腳位
```cpp
Sensor sensors[] = {
  {"V0", "Sensor1", 0, 100, "unit"},
  {"V1", "Sensor2", 0, 100, "unit"},
  {"V2", "Sensor3", 0, 100, "unit"},
  // 最多建議 10 個
};
const int sensorCount = 3;  // 更新數量
```

### 使用 MQTT（進階）
參考 `arduino_library/ESP_IoT_Manager_MQTT/` 中的函式庫

## 📚 相關文檔

- `DASHBOARD_README.md` - 儀表板功能說明
- `QUICKSTART_DASHBOARD.md` - 快速開始指南
- `MQTT_SETUP.md` - MQTT 設定說明

## ⚠️ 注意事項

1. **MAC 地址唯一性**：每個設備會自動使用自己的 MAC 地址，確保唯一性
2. **網路環境**：ESP8266/ESP32 和伺服器必須在同一網路
3. **電源供應**：USB 供電即可，測試時建議使用電腦 USB
4. **開發板選擇**：確保選擇正確的開發板型號
5. **序列埠衝突**：同時測試時需要連接到不同的 COM 端口

## 🎉 預期結果

成功運行後，你應該能看到：
- ✅ 兩個設備同時在線
- ✅ 總共 10 個數據流（每設備 5 個）
- ✅ 即時圖表自動更新
- ✅ 數據每 5 秒刷新一次
- ✅ WebSocket 連接正常
