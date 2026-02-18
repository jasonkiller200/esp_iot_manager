# ESP-IoT Manager - Web 即時監控介面

## 功能特色

### ✨ 即時監控儀表板
- **設備狀態總覽**: 即時顯示所有設備的線上/離線狀態
- **統計卡片**: 總設備數、線上設備、離線設備統計
- **自動刷新**: 每 30 秒自動更新設備狀態

### 📊 設備詳細監控
- **即時數據指標**: 顯示所有 DataStream 的最新值
- **Chart.js 圖表**: 即時趨勢圖，可選擇時間範圍（1小時/6小時/24小時/7天）
- **統計分析**: 自動計算最小值、最大值、平均值和數據點數
- **WebSocket 推送**: 新數據即時推送到前端，無需手動刷新

### 🔌 WebSocket 即時通訊
- **Socket.IO 整合**: 雙向即時通訊
- **設備狀態推送**: 設備上線/離線即時通知
- **數據即時更新**: 新數據自動更新圖表和數值
- **連線狀態指示器**: 顯示 WebSocket 連接狀態

## 快速開始

### 1. 啟動服務

```bash
python run.py
```

服務將在 `http://localhost:5000` 啟動

### 2. 訪問介面

#### 主儀表板
```
http://localhost:5000/dashboard
```
- 顯示所有設備概覽
- 設備列表和統計
- 快速導航

#### 設備詳細監控
```
http://localhost:5000/dashboard/device/{DEVICE_MAC}
```
- 替換 `{DEVICE_MAC}` 為實際設備 MAC 地址
- 例如: `http://localhost:5000/dashboard/device/AA:BB:CC:DD:EE:FF`

### 3. 測試 WebSocket 功能

執行測試腳本模擬設備發送數據：

```bash
python test_websocket.py
```

腳本會：
1. 自動創建測試 DataStream（溫度、濕度、氣壓）
2. 每 0.5-2 秒發送隨機模擬數據
3. 在瀏覽器中打開儀表板即可看到即時更新

## API 端點

### Dashboard API

#### 獲取所有設備
```
GET /dashboard/api/devices
```

回應範例：
```json
[
  {
    "mac": "AA:BB:CC:DD:EE:FF",
    "ip": "192.168.1.100",
    "version": "1.0.0",
    "chip_type": "ESP8266",
    "last_seen": "2024-02-18T12:30:00",
    "is_online": true
  }
]
```

#### 獲取設備的 DataStream
```
GET /dashboard/api/device/{device_mac}/datastreams
```

回應範例：
```json
[
  {
    "id": 1,
    "pin": "V0",
    "name": "Temperature",
    "data_type": "double",
    "min": 0,
    "max": 50,
    "unit": "°C",
    "latest_value": "25.5",
    "latest_time": "2024-02-18T12:30:00"
  }
]
```

#### 獲取歷史數據
```
GET /dashboard/api/device/{device_mac}/data/{pin}?hours=24&limit=100
```

參數：
- `hours`: 查詢最近幾小時的數據（預設 1）
- `limit`: 最多返回筆數（預設 100）

#### 獲取統計資訊
```
GET /dashboard/api/device/{device_mac}/stats?hours=24
```

回應範例：
```json
{
  "V0": {
    "name": "Temperature",
    "count": 144,
    "min": 20.5,
    "max": 29.8,
    "avg": 25.2,
    "latest": 25.5
  }
}
```

## WebSocket 事件

### 客戶端 → 伺服器

#### 訂閱設備更新
```javascript
socket.emit('subscribe_device', { device_mac: 'AA:BB:CC:DD:EE:FF' });
```

#### 請求即時數據
```javascript
socket.emit('request_data', { 
  device_mac: 'AA:BB:CC:DD:EE:FF',
  pin: 'V0'
});
```

### 伺服器 → 客戶端

#### 數據更新
```javascript
socket.on('data_update', (data) => {
  console.log(data);
  // {
  //   device_mac: 'AA:BB:CC:DD:EE:FF',
  //   pin: 'V0',
  //   value: '25.5',
  //   timestamp: '2024-02-18T12:30:00'
  // }
});
```

#### 設備狀態更新
```javascript
socket.on('device_status', (data) => {
  console.log(data);
  // {
  //   device_mac: 'AA:BB:CC:DD:EE:FF',
  //   status: { online: true, ip: '192.168.1.100' },
  //   timestamp: '2024-02-18T12:30:00'
  // }
});
```

## 技術架構

### 前端技術
- **Bootstrap 5**: UI 框架
- **Chart.js 3.9**: 即時圖表繪製
- **Socket.IO Client**: WebSocket 客戶端
- **Bootstrap Icons**: 圖標庫

### 後端技術
- **Flask**: Web 框架
- **Flask-SocketIO**: WebSocket 支援
- **SQLAlchemy**: ORM 資料庫操作
- **Paho MQTT**: MQTT 客戶端

## 數據流程

```
設備 (ESP8266/ESP32)
  ↓ MQTT/HTTP
MQTT Broker / Blynk API
  ↓
MQTT Manager / API Handler
  ↓
資料庫 (SQLite)
  ↓
WebSocket 廣播
  ↓
前端自動更新 (Chart.js)
```

## 瀏覽器要求

支援以下現代瀏覽器：
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

需要支援：
- WebSocket
- ES6 JavaScript
- CSS Grid / Flexbox

## 效能優化

### 前端
- 圖表數據點限制為 100 個（可調整）
- 自動刷新間隔：30 秒（儀表板）/ 10 秒（設備詳情）
- WebSocket 只推送訂閱的數據

### 後端
- 非阻塞 MQTT 客戶端
- 資料庫查詢限制和索引優化
- WebSocket 廣播使用異步處理

## 故障排除

### WebSocket 無法連接
1. 確認 Flask-SocketIO 已安裝：`pip install flask-socketio`
2. 確認沒有防火牆阻擋 5000 端口
3. 檢查瀏覽器控制台是否有錯誤訊息

### 圖表不顯示
1. 確認設備有發送數據
2. 檢查瀏覽器控制台的網路請求
3. 確認 DataStream 已正確創建

### 數據不即時更新
1. 確認 WebSocket 連接狀態（右上角指示器）
2. 檢查 MQTT Broker 是否正常運行
3. 查看伺服器日誌確認數據是否被接收

## 下一步開發

- [ ] 添加數據匯出功能（CSV/Excel）
- [ ] 支援自定義圖表顏色和樣式
- [ ] 添加警報和通知功能
- [ ] 支援多用戶和權限管理
- [ ] 移動端響應式優化
- [ ] 添加數據壓縮和歷史數據清理

## 授權

MIT License
