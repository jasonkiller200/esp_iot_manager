# Arduino 測試快速參考

## 🔧 快速設定（3 步驟）

### 1️⃣ 修改程式碼
```cpp
const char* ssid = "你的WiFi名稱";
const char* password = "你的WiFi密碼";
const char* serverUrl = "http://你的電腦IP:5000";
```

### 2️⃣ 上傳程式
- **NodeMCU**: 選擇板子 `NodeMCU 1.0`
- **ESP32**: 選擇板子 `ESP32 Dev Module`
- 鮑率：115200
- 點擊上傳

### 3️⃣ 查看結果
```
http://localhost:5000/dashboard
```

---

## 📊 設備資訊

| 設備 | 虛擬腳位 | 感測器數量 | 發送間隔 |
|------|---------|-----------|---------|
| NodeMCU (ESP8266) | V0-V4 | 5 個 | 5 秒 |
| ESP32 | V5-V9 | 5 個 | 5 秒 |

---

## 🎯 NodeMCU 感測器

| Pin | 感測器 | 範圍 |
|-----|--------|------|
| V0  | 溫度 | 15-35°C |
| V1  | 濕度 | 30-90% |
| V2  | 光線 | 0-1000 Lux |
| V3  | 土壤濕度 | 0-100% |
| V4  | 電池 | 3.0-4.2V |

---

## 🎯 ESP32 感測器

| Pin | 感測器 | 範圍 |
|-----|--------|------|
| V5  | CPU溫度 | 30-80°C |
| V6  | 氣壓 | 980-1040 hPa |
| V7  | 海拔 | 0-500 m |
| V8  | CO2 | 400-2000 ppm |
| V9  | WiFi信號 | -90~-30 dBm |

---

## 🔍 序列埠輸出範例

```
=====================================
  ESP8266 IoT Manager 測試程式
=====================================
MAC 地址: AA:BB:CC:DD:EE:FF

📡 連接 WiFi: MyWiFi
✅ WiFi 連接成功！
   IP 地址: 192.168.1.101

📝 創建 DataStream 定義...
   ✅ Temperature (V0)
   ✅ Humidity (V1)
   ...

📊 [5s] ESP8266 發送數據：
   ✅ Temperature: 25.34 °C
   ✅ Humidity: 65.72 %
   ...
✓ 成功: 5/5 | 耗時: 312ms
```

---

## ⚡ 常見問題

### WiFi 連不上？
- 檢查 SSID/密碼
- 確認是 2.4GHz WiFi
- ESP8266 不支援 5GHz

### 數據送不出去？
- 檢查伺服器 IP
- 確認 IoT Manager 在運行
- 檢查防火牆設定

### 找不到序列埠？
- 安裝 USB 驅動（CP2102/CH340）
- 重新插拔 USB
- 檢查裝置管理員

---

## 📱 查看監控介面

### 主儀表板
```
http://localhost:5000/dashboard
```
顯示所有設備狀態

### 設備詳情（需替換 MAC）
```
http://localhost:5000/dashboard/device/[MAC地址]
```
顯示即時圖表和數據

---

## 💡 小技巧

1. **同時測試兩個設備**
   - 使用兩條 USB 線
   - 分別連接 NodeMCU 和 ESP32
   - 同時上傳並運行

2. **修改發送頻率**
   ```cpp
   const unsigned long sendInterval = 3000;  // 3秒
   ```

3. **查看 MAC 地址**
   - 打開序列埠監控視窗
   - 重啟設備
   - 第一行會顯示 MAC 地址

4. **測試單一感測器**
   - 修改 `sensors[]` 陣列
   - 只保留需要的感測器
   - 更新 `sensorCount`

---

## 📞 取得協助

- 詳細說明：`arduino_client/README.md`
- 儀表板文檔：`DASHBOARD_README.md`
- 快速開始：`QUICKSTART_DASHBOARD.md`
