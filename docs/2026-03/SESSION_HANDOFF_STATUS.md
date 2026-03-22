# Session Handoff Status

最後更新：2026-03-22

## 1) 目前完成狀態

### CI/CD

- CI 已上線：`.github/workflows/ci.yml`
  - `py_compile` + `pytest tests -q`
- CD 已上線：`.github/workflows/deploy.yml`
  - `push master` -> staging（secrets 齊全時）
  - `workflow_dispatch` -> staging / production（production 手動）
- CD 設定文件：`CD_SETUP.md`

### 安全與設定

- 寫入/控制 token 保護已套用（`require_write_token`）
- env-first 設定已落地：`config.py`, `.env.example`
- 安全說明文件：`SECURITY_BASELINE.md`

### 數據與資料庫

- 已導入 `HourlyAggregate` 與小時聚合策略
- 已有聚合與清理腳本：`aggregate_data.py`
- Dashboard 支援 `source=auto`（<=24h raw，>24h hourly）
- DB 索引優化與 migration 已完成

### 控制可靠性

- 命令 lifecycle：`queued/sent/ack/timeout/failed`
- 命令追蹤模型：`app/models/command.py`
- 控制白名單 + pin/value 驗證已上線
- 審計欄位（操作者 `requested_by`）已上線

### 前端（商轉升級）

- `dashboard/live` 已升級 NOC 牆
  - 告警排序
  - 大屏模式
  - 事件側欄
  - 分頁輪播
  - 群組篩選（ESP32/ESP8266/Unknown）
  - 告警聲音開關

### 維運與交付

- 部署模板：`docker-compose.yml`
- MQTT 容器配置：`mosquitto/config/*`
- 備份還原工具：`backup_restore.py`
- 部署文件：`DEPLOYMENT_WEEK4.md`, `SCHEDULER_SETUP.md`

### 測試

- `tests` 目前可通過（4 passed）
- 測試說明：`RUNBOOK_TESTS.md`

---

## 2) 最新推送資訊

- Branch: `master`
- Latest commit: `c467fe7`
- Remote: `origin/master`

---

## 3) 尚未完成（下次接續）

### P0

1. GitHub branch protection / environment protection 實際啟用
2. staging secrets 設定並打通 CD 自動部署
3. staging 回滾演練（至少一次）

### P1

4. MQTT ACL 正式策略與驗證
5. RBAC 正式登入系統（viewer/operator/admin）
6. OTA 完整性驗證（hash/signature）

### P2

7. 擴充 API/控制流程測試覆蓋
8. production deploy 審核流程與 SOP 收斂

---

## 4) 下次開工建議順序

1. 先做「GitHub 保護規則 + staging secrets」
2. 觸發一次 push，驗證 staging 自動部署
3. 跑健康檢查：
   - `/api/health`
   - `/api/ready`
   - `/dashboard/admin/db-health`
4. 做一次 rollback 演練並記錄結果

---

## 5) 重要檔案索引

- 計畫總表：`COMMERCIALIZATION_4W_PLAN.md`
- 安全基線：`SECURITY_BASELINE.md`
- CD 設定：`CD_SETUP.md`
- 部署落地：`DEPLOYMENT_WEEK4.md`
- DB 優化：`DATABASE_OPTIMIZATION.md`
- 測試 Runbook：`RUNBOOK_TESTS.md`
