# Security Baseline（Week 1）

本文件說明目前已落地的安全基線與部署設定方式。

## 1) 寫入/控制 API 保護

已保護端點（需 `WRITE_API_TOKEN`）：

- `/upload`
- `/firmware/delete/<id>`
- `/firmware/set_latest/<id>`
- `/device/push_update/<id>`
- `/dashboard/device/<mac>/edit`
- `/dashboard/device/<mac>/delete`
- `/dashboard/datastream/<id>/edit`
- `/dashboard/device/<mac>/control`
- `/dashboard/device/<mac>/reboot`

支援 token 傳遞方式：

- Header: `Authorization: Bearer <token>`
- Header: `X-API-Token: <token>`
- HTML Form: `write_token` hidden field

## 2) 環境變數

請複製 `.env.example` 為 `.env` 後填值：

```bash
copy .env.example .env
```

至少必填：

- `SECRET_KEY`
- `WRITE_API_TOKEN`
- `DATABASE_URL`（正式建議 PostgreSQL）

## 3) 前端 Token 使用

管理頁（`/`）提供「管理寫入 Token」輸入欄位，儲存後會寫入瀏覽器 localStorage：

- key: `esp_write_token`

Dashboard 的寫入操作會自動帶上 `X-API-Token`。

## 4) 啟動模式

`run.py` 已改為依 `FLASK_DEBUG` 控制 debug。生產環境請使用：

- `FLASK_ENV=production`
- `FLASK_DEBUG=0`

## 5) 生產安全檢查

App 啟動時會檢查以下項目並記錄 warning：

- `SECRET_KEY` 是否仍為預設值
- `WRITE_API_TOKEN` 是否為空
