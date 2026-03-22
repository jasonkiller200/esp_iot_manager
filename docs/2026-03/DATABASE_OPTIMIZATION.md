# 數據庫容量優化計劃（最終維度：小時）

## 目標

本計劃採用「Raw + Hourly」雙層架構，並將**小時級聚合作為最終長期保存層**。

- Raw `DataPoint`：保留短期即時與除錯資料
- `HourlyAggregate`：保留長期趨勢查詢與報表資料
- 不再引入 day 級最終層，避免多層聚合造成維護成本與精度損失

---

## 現狀與風險

- 目前 `DataPoint` 持續累積，無自動過期與壓縮機制
- 每分鐘上傳（10 device × 5 pin）約 72,000 筆/天
- 約 1 個月 200 萬筆，SQLite 查詢與索引維護成本快速上升

---

## 新的保留策略（建議）

| 層級 | 用途 | 保留期限 | 查詢場景 |
|------|------|----------|----------|
| Raw (`DataPoint`) | 即時監控、故障排查 | 7 天（可調） | 最近 24h ~ 7d |
| Hourly (`HourlyAggregate`) | 長期趨勢與統計 | 1~2 年或永久 | 7d 以上 |

> 關鍵原則：**最終壓縮維度固定為小時**。

---

## 實作內容（已落地）

### 1) 新增小時聚合模型

- 檔案：`app/models/datastream.py`
- 模型：`HourlyAggregate`
- 聚合欄位：
  - `count`
  - `min_value`
  - `max_value`
  - `avg_value`
  - `last_value`
- 唯一鍵：`(device_mac, pin, hour_bucket)`

### 2) 新增聚合與清理腳本

- 檔案：`aggregate_data.py`
- 功能：
  1. 將近期 Raw 依小時分桶寫入 `HourlyAggregate`
  2. 刪除保留天數外的 Raw

執行：

```bash
python aggregate_data.py
```

安全模式（建議先 dry run）：

```bash
python aggregate_data.py --dry-run
python aggregate_data.py --full-backfill
```

參數說明：

- `--raw-keep-days N`：Raw 保留天數（預設 7）
- `--lookback-days N`：聚合來源視窗（預設 14）
- `--full-backfill`：全量回補（等同極大 lookback）
- `--dry-run`：只顯示估算，不寫資料
- `--force-delete-if-no-aggregate`：即使未產出小時聚合仍強制刪 raw（不建議）

### 3) Dashboard API 支援小時來源

- 檔案：`app/routes/dashboard.py`
- API：`GET /dashboard/api/device/<mac>/data/<pin>?source=hourly`

### 4) 前端資料來源選單切換為小時聚合

- 檔案：`app/templates/device_detail.html`
- 原本 `aggregated` 改為 `hourly`

---

## 建議排程

目前專案可先以 OS 排程執行 `aggregate_data.py`：

- 每 30 分鐘或每 1 小時執行一次
- 建議在離峰時段再加跑一次完整回補（例如每日凌晨）

Windows Task Scheduler（範例）：

```bash
venv\Scripts\python.exe D:\ai_develop\esp_iot_manager\aggregate_data.py
```

---

## 實務上主流 IoT 平台做法（精簡）

多數平台採用一致策略：

1. 短期保留 Raw（熱資料）
2. 以固定時間桶做下採樣（1m/5m/1h）
3. 長期查詢命中聚合層
4. 用 TTL/Retention 自動清理

常見對應：

- InfluxDB：Retention Policy + Task/Continuous Query 下採樣
- TimescaleDB：Continuous Aggregates + Retention
- AWS IoT（搭配 Timestream）：Memory/磁碟層保留策略 + 分層查詢
- Azure IoT（搭配 Data Explorer/TSI）：Materialized View + TTL

你目前規模下，先維持 SQLite + 小時聚合是合理且低成本的第一階段。

---

## 下一步建議

1. 建立 migration（新增 `HourlyAggregate` 表）
2. 佈署排程（每小時跑一次）
3. API 加入自動來源切換：
   - `<=24h` 用 Raw
   - `>24h` 預設用 Hourly
4. 當設備量或寫入量再上升時，評估遷移到 TimescaleDB / InfluxDB
