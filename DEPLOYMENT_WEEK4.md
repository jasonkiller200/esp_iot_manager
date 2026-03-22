# Week 4 部署與維運落地

本文件提供可直接執行的部署、健康檢查、備份還原與驗證流程。

## 1) 前置設定

1. 複製環境檔：

```bash
copy .env.example .env
```

2. 填寫必要參數：

- `SECRET_KEY`
- `WRITE_API_TOKEN`
- `MQTT_USERNAME` / `MQTT_PASSWORD`
- `CONTROL_PIN_WHITELIST`

## 2) Docker Compose 啟動

```bash
docker compose up -d
```

服務：

- App: `http://localhost:5000`
- MQTT: `localhost:1883`

## 3) 健康檢查

- DB 健康：`GET /dashboard/admin/db-health`

範例：

```bash
curl http://127.0.0.1:5000/dashboard/admin/db-health
```

## 4) 排程

參考：`SCHEDULER_SETUP.md`

- 每小時跑：`aggregate_data.py`
- 每日 dry-run：`aggregate_data.py --dry-run --full-backfill`

## 5) 備份與還原

### 備份

```bash
venv\Scripts\python.exe backup_restore.py backup
```

### 還原

```bash
venv\Scripts\python.exe backup_restore.py restore --file backups\esp_iot_backup_YYYYMMDD_HHMMSS.zip
```

## 6) 上線驗收清單

- [ ] 未授權 token 無法寫入/控制
- [ ] 命令 lifecycle 可看到 `queued/sent/ack/timeout/failed`
- [ ] 超過 24h 查詢自動改用 hourly
- [ ] 聚合排程可穩定執行
- [ ] 備份檔可完成還原
