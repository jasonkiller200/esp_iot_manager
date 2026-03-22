# ESP IoT Manager 部署與優化建議報告

本報告針對 **ESP IoT Manager** 專案，從 Linux 系統部署方案到專案架構優化進行了深度分析。旨在提升系統的穩定性、擴充性與安全性。

---

## 第一部分：Linux 系統部署方案 (Production Ready)

建議採用 `Nginx + Gunicorn + Mosquitto + Systemd` 的生產級技術棧進行部署。

### 1. 系統環境準備
在 Ubuntu/Debian 系統上安裝基礎組件：
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx mosquitto mosquitto-clients redis-server -y
```

### 2. MQTT Broker (Mosquitto) 配置
修改 `/etc/mosquitto/mosquitto.conf`，確保安全性：
*   **關閉匿名訪問：** `allow_anonymous false`
*   **設置密碼檔：** `password_file /etc/mosquitto/passwd`
*   **持久化數據：** 確保開啟 `persistence true` 以保留訂閱狀態。

### 3. 專案環境搭建
```bash
cd /var/www/esp-iot-manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn eventlet  # 支援非同步 Worker
```

### 4. 進程管理 (Systemd)
創建 `/etc/systemd/system/esp_iot.service`：
```ini
[Unit]
Description=Gunicorn instance to serve ESP IoT Manager
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/esp-iot-manager
Environment="PATH=/var/www/esp-iot-manager/venv/bin"
# 針對 SocketIO 或長連接建議使用 eventlet worker
ExecStart=/var/www/esp-iot-manager/venv/bin/gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:5000 run:app

[Install]
WantedBy=multi-user.target
```

### 5. Nginx 反向代理配置
配置 Nginx 處理靜態文件並支持 WebSocket 轉發，這對即時 Dashboard 至關重要。

---

## 第二部分：專案優化建議報告

### 1. 核心架構優化 (Architectural Enhancements)
*   **非同步任務處理：**
    *   現狀：MQTT 消息處理與 API 請求共用 Flask 進程。
    *   建議：引入 **Celery + Redis**。將耗時的「數據存檔」與「自動化邏輯」轉移到後台 Worker，避免阻塞。
*   **時序數據存儲 (Time-series Data)：**
    *   建議：針對 `datastream` 表，當數據量達到萬級以上時，建議將 SQLite/MySQL 遷移至 **TimescaleDB** (PostgreSQL 插件)，能顯著提升傳感器歷史數據的查詢速度。
*   **快取機制：**
    *   使用 Redis 存儲裝置的 **「最新在線狀態 (Heartbeat)」** 與 **「即時讀數」**，減少對主資料庫的頻繁讀取。

### 2. 安全性加強 (Security)
*   **通信加密：**
    *   **MQTT TLS/SSL：** 強制要求 ESP 裝置使用 8883 埠進行加密通訊，防止 WiFi 環境下的抓包風險。
    *   **HTTPS：** 使用 Let's Encrypt 為 Nginx 配置免費 SSL 憑證。
*   **API 保護：**
    *   在 `blynk_api.py` 中實施嚴格的 **Rate Limiting** (頻率限制)，防止針對裝置 Token 的暴力破解。
*   **韌體簽章：**
    *   在 Firmware 上傳時計算雜湊值 (SHA-256)，裝置端下載後進行校驗，確保 OTA 更新過程未被篡改。

### 3. 裝置管理優化 (Device Management)
*   **MQTT 遺言 (LWT) 機制：**
    *   優化 `mqtt_manager.py`。利用 MQTT 的 **Last Will and Testament** 功能，當裝置異常離線時，Broker 能自動發布離線消息，系統第一時間更新資料庫狀態。
*   **影子設備 (Device Shadow)：**
    *   實現影子設備邏輯。當用戶下達指令時，若裝置離線，指令存於伺服器；待裝置重連後，自動同步狀態。

### 4. 前端與用戶體驗 (Frontend & UX)
*   **前後端分離 (SPA)：**
    *   目前使用 Jinja2 渲染。隨著功能增加，建議將前端遷移至 **Vue.js** 或 **React**。
    *   優點：提供更流暢的交互體驗（如拖拽式儀表板），並讓後端專注於 API 提供。
*   **即時通訊：**
    *   確保 Dashboard 數據更新採用 **WebSocket (Flask-SocketIO)**，而非傳統的 Ajax 輪詢，降低伺服器壓力。

### 5. 維運與監控 (DevOps)
*   **Docker 化部署：**
    *   編寫 `docker-compose.yml` 將 Flask、Mosquitto、DB 容器化，解決「在我的電腦能跑，在伺服器不能跑」的問題。
*   **結構化日誌：**
    *   引入 `structlog` 記錄 MQTT 的通信細節，便於日後追蹤特定裝置的連接不穩定問題。

---

## 第三部分：優先執行清單 (Roadmap)

1.  **[高優先級]** 生成 `requirements.txt` 並完成 Dockerfile 編寫。
2.  **[中優先級]** 在 `mqtt_manager.py` 中完善 LWT (遺言) 機制，確保在線狀態準確。
3.  **[中優先級]** 為 API 路由（尤其是 Blynk 模擬接口）添加單元測試。
4.  **[低優先級]** 評估時序數據量，決定是否引入 TimescaleDB。

---
**報告編寫人：** Gemini CLI (Senior SE)
**日期：** 2026年3月1日
