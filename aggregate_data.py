"""
資料聚合與清理工具

策略：
- Raw DataPoint: 僅保留短期（預設 7 天）
- HourlyAggregate: 作為最終長期層（小時維度）
"""

import argparse
from datetime import datetime, timezone, timedelta
from sqlalchemy import func

from app import create_app, db
from app.models.datastream import DataPoint, HourlyAggregate

TAIPEI_TZ = timezone(timedelta(hours=8))


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def hour_floor(ts):
    return ts.replace(minute=0, second=0, microsecond=0)


def upsert_hourly_aggregate(device_mac, pin, bucket, values, last_value):
    row = HourlyAggregate.query.filter_by(
        device_mac=device_mac,
        pin=pin,
        hour_bucket=bucket,
    ).first()

    if row is None:
        row = HourlyAggregate()
        row.device_mac = device_mac
        row.pin = pin
        row.hour_bucket = bucket
        db.session.add(row)

    row.count = len(values)
    row.min_value = min(values)
    row.max_value = max(values)
    row.avg_value = sum(values) / len(values)
    row.last_value = str(last_value)


def aggregate_raw_to_hourly(raw_keep_days=7, lookback_days=14):
    now = datetime.now(TAIPEI_TZ)
    agg_cutoff = now - timedelta(days=lookback_days)
    delete_cutoff = now - timedelta(days=raw_keep_days)

    points = (
        DataPoint.query.filter(DataPoint.timestamp >= agg_cutoff)
        .order_by(
            DataPoint.device_mac.asc(), DataPoint.pin.asc(), DataPoint.timestamp.asc()
        )
        .all()
    )

    grouped = {}
    for p in points:
        numeric = to_float(p.value)
        if numeric is None:
            continue

        bucket = hour_floor(p.timestamp)
        key = (p.device_mac, p.pin, bucket)
        item = grouped.get(key)
        if item is None:
            grouped[key] = {
                "values": [numeric],
                "last_value": p.value,
            }
        else:
            item["values"].append(numeric)
            item["last_value"] = p.value

    upsert_count = 0
    for (device_mac, pin, bucket), item in grouped.items():
        upsert_hourly_aggregate(
            device_mac,
            pin,
            bucket,
            item["values"],
            item["last_value"],
        )
        upsert_count += 1

    db.session.commit()

    deleted = DataPoint.query.filter(DataPoint.timestamp < delete_cutoff).delete()
    db.session.commit()

    return {
        "upserted_hourly": upsert_count,
        "deleted_raw": deleted,
        "raw_keep_days": raw_keep_days,
        "lookback_days": lookback_days,
    }


def aggregate_raw_to_hourly_safe(
    raw_keep_days=7,
    lookback_days=14,
    dry_run=False,
    force_delete_if_no_aggregate=False,
):
    now = datetime.now(TAIPEI_TZ)
    agg_cutoff = now - timedelta(days=lookback_days)
    delete_cutoff = now - timedelta(days=raw_keep_days)

    points = (
        DataPoint.query.filter(DataPoint.timestamp >= agg_cutoff)
        .order_by(
            DataPoint.device_mac.asc(), DataPoint.pin.asc(), DataPoint.timestamp.asc()
        )
        .all()
    )

    grouped = {}
    non_numeric_count = 0
    for p in points:
        numeric = to_float(p.value)
        if numeric is None:
            non_numeric_count += 1
            continue

        bucket = hour_floor(p.timestamp)
        key = (p.device_mac, p.pin, bucket)
        item = grouped.get(key)
        if item is None:
            grouped[key] = {
                "values": [numeric],
                "last_value": p.value,
            }
        else:
            item["values"].append(numeric)
            item["last_value"] = p.value

    upsert_count = len(grouped)

    if dry_run:
        return {
            "dry_run": True,
            "source_points_in_lookback": len(points),
            "non_numeric_points": non_numeric_count,
            "would_upsert_hourly": upsert_count,
            "would_delete_raw": DataPoint.query.filter(
                DataPoint.timestamp < delete_cutoff
            ).count(),
            "raw_keep_days": raw_keep_days,
            "lookback_days": lookback_days,
        }

    for (device_mac, pin, bucket), item in grouped.items():
        upsert_hourly_aggregate(
            device_mac,
            pin,
            bucket,
            item["values"],
            item["last_value"],
        )

    db.session.commit()

    delete_query = DataPoint.query.filter(DataPoint.timestamp < delete_cutoff)
    delete_target_count = delete_query.count()

    if (
        delete_target_count > 0
        and upsert_count == 0
        and not force_delete_if_no_aggregate
    ):
        return {
            "upserted_hourly": upsert_count,
            "deleted_raw": 0,
            "delete_skipped": True,
            "reason": "no hourly data generated; skip raw deletion for safety",
            "source_points_in_lookback": len(points),
            "non_numeric_points": non_numeric_count,
            "raw_keep_days": raw_keep_days,
            "lookback_days": lookback_days,
        }

    deleted = delete_query.delete()
    db.session.commit()

    return {
        "upserted_hourly": upsert_count,
        "deleted_raw": deleted,
        "source_points_in_lookback": len(points),
        "non_numeric_points": non_numeric_count,
        "raw_keep_days": raw_keep_days,
        "lookback_days": lookback_days,
        "force_delete_if_no_aggregate": force_delete_if_no_aggregate,
    }


def show_stats():
    raw_count = DataPoint.query.count()
    hourly_count = HourlyAggregate.query.count()
    latest_hour = db.session.query(func.max(HourlyAggregate.hour_bucket)).scalar()
    return {
        "raw_count": raw_count,
        "hourly_count": hourly_count,
        "latest_hour_bucket": latest_hour.isoformat() if latest_hour else None,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Aggregate DataPoint to HourlyAggregate"
    )
    parser.add_argument(
        "--raw-keep-days", type=int, default=7, help="Keep raw data for N days"
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=14,
        help="Aggregate source lookback window (days)",
    )
    parser.add_argument(
        "--full-backfill", action="store_true", help="Aggregate all available raw data"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show plan only, no data changes"
    )
    parser.add_argument(
        "--force-delete-if-no-aggregate",
        action="store_true",
        help="Allow deleting old raw data even when no hourly rows generated",
    )
    args = parser.parse_args()

    lookback_days = args.lookback_days
    if args.full_backfill:
        lookback_days = 36500

    app = create_app()
    with app.app_context():
        result = aggregate_raw_to_hourly_safe(
            raw_keep_days=args.raw_keep_days,
            lookback_days=lookback_days,
            dry_run=args.dry_run,
            force_delete_if_no_aggregate=args.force_delete_if_no_aggregate,
        )
        stats = show_stats()
        print("[aggregate] done:")
        print(result)
        print("[stats]")
        print(stats)
