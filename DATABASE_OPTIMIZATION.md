# 數據庫容量優化計劃

## 問題描述

目前 `DataPoint` 模型存儲所有設備的所有數據點，沒有過期機制。當設備數量增加時，數據庫會快速膨脹。

### 現狀評估
- 每個設備多個 Virtual Pin（V0, V1, V2...）
- 每分鐘上傳數據，假設 10 個設備 × 5 個 pin × 1 筆/分 × 60分 × 24小時 = 72,000 筆/天
- 1 個月 ≈ 200 萬筆，1 年 ≈ 2,400 萬筆
- SQLite 在百萬級別效能會明顯下降

---

## 解決方案

### 方案 1：數據自動清理 (最簡單)

在 `app/__init__.py` 或定期腳本中加入：

```python
# 保留 30 天數據
from datetime import datetime, timedelta
from app.models.datastream import DataPoint

def cleanup_old_data(days=30):
    cutoff = datetime.now() - timedelta(days=days)
    deleted = DataPoint.query.filter(DataPoint.timestamp < cutoff).delete()
    db.session.commit()
    return deleted
```

### 方案 2：數據聚合 (推薦)

保留原始數據 7 天後，自動轉換為小時/天級統計值：

| 數據類型 | 保留期限 |
|---------|---------|
| 原始數據 | 7 天 |
| 小時統計 | 90 天 |
| 天統計 | 無限 |

### 方案 3：遷移到專業時序數據庫

| 數據庫 | 優點 | 適用場景 |
|--------|------|---------|
| InfluxDB | 專為時序設計、壓縮率高 | 大規模 IoT |
| TimescaleDB | PostgreSQL 插件、SQL 相容 | 需要複雜查詢 |
| ClickHouse | 極速分析、壓縮率高 | 大數據分析 |

---

## 實作優先順序

1. **[高]** 實作數據自動清理（30天）
2. **[中]** 加入數據聚合機制
3. **[低]** 評估遷移至 InfluxDB

---

## 參考資源

- [InfluxDB Python Client](https://github.com/influxdata/influxdb-client-python)
- [TimescaleDB 時序數據庫](https://www.timescale.com/)
