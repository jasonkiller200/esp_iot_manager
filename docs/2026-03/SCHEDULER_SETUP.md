# 排程設定（Windows Task Scheduler）

本專案目前使用 `aggregate_data.py` 進行小時聚合與 Raw 清理。

## 建議排程

1. 每 1 小時執行一次（正式）
2. 每日凌晨執行一次 full backfill dry-run（驗證）

## 指令

### 每小時聚合

```bash
venv\Scripts\python.exe D:\ai_develop\esp_iot_manager\aggregate_data.py
```

### 每日檢查（不改資料）

```bash
venv\Scripts\python.exe D:\ai_develop\esp_iot_manager\aggregate_data.py --dry-run --full-backfill
```

## 建立排程（GUI）

1. 開啟 Task Scheduler
2. 建立基本工作：
   - 名稱：`esp_iot_hourly_aggregate`
   - 觸發條件：每 1 小時
   - 動作：啟動程式
3. 程式/指令碼：
   - `D:\ai_develop\esp_iot_manager\venv\Scripts\python.exe`
4. 引數：
   - `D:\ai_develop\esp_iot_manager\aggregate_data.py`
5. 起始於：
   - `D:\ai_develop\esp_iot_manager`

## 驗證

執行後可檢查：

- `GET /dashboard/admin/db-health`
- script 輸出中的 `upserted_hourly` 與 `deleted_raw`
