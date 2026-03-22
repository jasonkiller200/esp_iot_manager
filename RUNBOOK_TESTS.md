# 測試與驗證 Runbook

## 1) 安裝測試依賴

```bash
venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## 2) 執行單元測試

```bash
venv\Scripts\python.exe -m pytest tests -q
```

## 3) 基本健康檢查

啟動後可檢查：

- `GET /api/health`
- `GET /api/ready`
- `GET /dashboard/admin/db-health`

範例：

```bash
curl http://127.0.0.1:5000/api/health
curl http://127.0.0.1:5000/api/ready
curl http://127.0.0.1:5000/dashboard/admin/db-health
```
