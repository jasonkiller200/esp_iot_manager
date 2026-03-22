# ESP IoT Manager 商轉前 4 週執行清單

本清單以「先上線安全、再上線穩定、最後上線可營運」為順序。

---

## 目標與範圍

- 目標：在 4 週內把目前 MVP 版本提升到可試營運的基線
- 範圍：Backend/API、MQTT 控制、資料庫、Dashboard、Firmware library、維運流程
- 不含：大規模多租戶計費模組、跨區部署、企業 SSO

---

## Week 1：安全基線（必做）

### 任務

1. 導入登入驗證與角色權限（RBAC）
   - 角色建議：`viewer` / `operator` / `admin`
   - 高風險操作（刪設備、reboot、下控制）需 `operator` 以上
2. 所有寫入 API 加入 CSRF 或 API token 驗證（依使用情境擇一）
3. 配置改為環境變數（移除硬編碼 secret）
4. 關閉 debug/unsafe 啟動模式，切換正式 WSGI 啟動
5. MQTT broker 開啟帳密 + topic ACL（每設備最小權限）
6. OTA 增加完整性保護（至少 SHA256；建議簽章驗證）

### 驗收標準

- 未登入無法呼叫 `/dashboard/device/<mac>/control`、`/reboot`、`/delete`
- `SECRET_KEY`、MQTT 帳密、DB URI 全部來自 env
- 正式模式啟動不含 `debug=True` / `allow_unsafe_werkzeug=True`
- 設備只能 publish/subscribe 自己 topic，不可跨設備控制
- OTA 韌體下載前有 checksum 或 signature 驗證

### 主要修改檔案

- `config.py`
- `run.py`
- `app/__init__.py`
- `app/routes/dashboard.py`
- `app/routes/main.py`
- `mosquitto_config_template.conf`

---

## Week 2：資料與效能基線

### 任務

1. DB 切換至 PostgreSQL（至少 staging/prod）
2. 完整 migration 與索引補齊
   - `data_point(device_mac, pin, timestamp)`
   - `hourly_aggregate(device_mac, pin, hour_bucket)`
3. 聚合與清理流程排程化
   - 每小時執行 `aggregate_data.py`
   - 每日做一次 full-backfill 安全檢查
4. 刪設備時同步刪除 `HourlyAggregate`
5. MQTT 寫入改批次 commit（減少每筆 commit）

### 驗收標準

- 72 小時壓測下 API 延遲穩定、資料無遺失
- 刪設備後 `DataPoint`/`DataStream`/`HourlyAggregate` 都清乾淨
- 聚合任務連續執行 3 天無錯誤
- 近 7 天查詢走 raw、長時段查詢走 hourly

### 主要修改檔案

- `app/models/datastream.py`
- `app/routes/dashboard.py`
- `app/mqtt_manager.py`
- `aggregate_data.py`
- `migrations/versions/*.py`

---

## Week 3：控制可靠性與可追蹤

### 任務

1. 命令加入 `command_id` 與狀態追蹤
   - `queued` / `sent` / `ack` / `timeout` / `failed`
2. 裝置側 ACK 回報（成功/失敗與錯誤碼）
3. Dashboard 顯示命令結果與最後回應時間
4. 操作審計紀錄（who/when/what/target/result）
5. 下發控制加入白名單檢查與參數驗證（pin/value）

### 驗收標準

- 每筆控制命令在 UI 可查到完整生命周期
- reboot/control 有可查詢 audit trail
- 非白名單 pin 或非法 value 一律拒絕
- 裝置離線時命令有 timeout 回報，不會無限 pending

### 主要修改檔案

- `app/routes/dashboard.py`
- `app/mqtt_manager.py`
- `app/templates/device_detail.html`
- `app/static/js/dashboard-widgets.js`
- `arduino_library/ESP_IoT_Manager/src/ESP_IoT_Manager.h`
- `arduino_library/ESP_IoT_Manager/src/ESP_IoT_Manager.cpp`

---

## Week 4：維運與交付基線

### 任務

1. 建立部署流程（Docker Compose 或 systemd + Nginx）
2. 健康檢查與監控告警
   - API health
   - MQTT 連線狀態
   - DB 連線與慢查詢
3. 建立備份/還原流程（DB + firmware）
4. 自動化測試與 CI
   - API smoke test
   - 控制流程整合測試
5. 發布文件與 SOP
   - 部署手冊
   - 故障排除手冊
   - 回滾手冊

### 驗收標準

- 可一鍵部署到新環境（不手改程式）
- 有基本儀表板可看健康度與錯誤率
- 備份檔可在演練環境成功還原
- PR 必須通過測試才可合併

### 主要修改檔案

- `DEPLOYMENT_AND_OPTIMIZATION.md`
- `ROADMAP.md`
- `tests/*`
- `docker-compose.yml`（若新增）
- `.github/workflows/*`（若新增）

---

## PR 建議順序（可直接執行）

1. `security-baseline-auth-rbac`
2. `config-env-and-prod-runner`
3. `mqtt-acl-and-ota-integrity`
4. `postgres-migration-and-indexes`
5. `hourly-retention-scheduler-hardening`
6. `command-tracking-and-ack`
7. `audit-log-and-control-validation`
8. `ops-monitoring-backup-ci`

---

## 風險與緩解

- 風險：SQLite 在高寫入下鎖競爭嚴重
  - 緩解：Week 2 優先切 PostgreSQL
- 風險：控制命令無 ACK 導致運維誤判
  - 緩解：Week 3 強制 command lifecycle
- 風險：缺權限造成誤操作或惡意控制
  - 緩解：Week 1 先上 RBAC + ACL

---

## 建議 KPI（試營運）

- 設備上線率（24h）> 98%
- 命令成功 ACK 率 > 99%
- 控制命令 P95 延遲 < 2 秒
- API 5xx 比例 < 0.5%
- 聚合任務成功率 = 100%
