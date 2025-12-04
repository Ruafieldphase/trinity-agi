#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Timeseries Collector (Phase 6 Week 1)

Collects monitoring metrics at a fixed interval and stores them into SQLite by default.
Optionally supports writing to InfluxDB if connection arguments are provided.

Data source:
- Uses the most recent of:
  - outputs/monitoring_metrics_latest.json (produced by generate_monitoring_report.ps1)
  - outputs/quick_status_latest.json (produced by quick_status.ps1 when exporting)

Storage:
- SQLite (default): outputs/timeseries_metrics.db, table: metrics
- InfluxDB (optional): requires --influx-url, --influx-org, --influx-bucket and token via --influx-token or env INFLUXDB_TOKEN

Run examples:
  python scripts/timeseries_collector.py --once
  python scripts/timeseries_collector.py --interval 60

Windows PowerShell tasks already generate the JSON sources. If not present, the collector waits
and retries unless --once is provided.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sqlite3
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
OUTPUTS_DIR = os.path.join(WORKSPACE_ROOT, "outputs")
DEFAULT_SQLITE_PATH = os.path.join(OUTPUTS_DIR, "timeseries_metrics.db")
DEFAULT_TABLE = "metrics"

SOURCE_FILES = [
    os.path.join(OUTPUTS_DIR, "monitoring_metrics_latest.json"),
    os.path.join(OUTPUTS_DIR, "quick_status_latest.json"),
]

STOP_REQUESTED = False


def _setup_signals():
    def _handler(signum, frame):
        global STOP_REQUESTED
        STOP_REQUESTED = True
    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def find_latest_source(preferred: Optional[str] = None) -> Optional[str]:
    candidates = []
    if preferred:
        p = os.path.join(OUTPUTS_DIR, preferred)
        if os.path.isfile(p):
            candidates.append(p)
    for f in SOURCE_FILES:
        if os.path.isfile(f):
            candidates.append(f)
    if not candidates:
        return None
    # pick most recently modified
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates[0]


def load_metrics_json(path: str) -> Dict[str, Any]:
    # Use utf-8-sig to tolerate BOM in generated files
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


# Heuristic extraction across known formats
HEALTH_MAP = {"EXCELLENT": 1.0, "GOOD": 0.8, "DEGRADED": 0.5, "CRITICAL": 0.2}


def extract_fields(doc: Dict[str, Any]) -> Dict[str, Any]:
    # timestamp
    ts = doc.get("timestamp") or doc.get("generated_at") or _now_iso()

    # health status / score
    status = (doc.get("OverallHealth") or doc.get("Overall_Status") or doc.get("overall_health")
              or doc.get("health") or doc.get("status") or "UNKNOWN")
    if isinstance(status, dict):
        status = status.get("status") or status.get("level") or "UNKNOWN"
    status_str = str(status).upper()
    health_score = HEALTH_MAP.get(status_str, None)

    # availability (percent)
    availability = (doc.get("availability") or doc.get("GatewayAvailability")
                    or doc.get("gateway_availability") or doc.get("Availability"))

    # latency (p95)
    latency = (doc.get("p95_latency_ms") or doc.get("latency_p95_ms")
               or _nested_lookup(doc, [
                   ("Metrics", "LatencyP95Ms"),
                   ("performance", "latency_p95_ms"),
               ]))

    # alerts severity counts
    alerts = doc.get("alerts") or doc.get("Alerts") or {}
    critical = _from_many(alerts, ["critical", "Critical", "CRITICAL"], default=0)
    warning = _from_many(alerts, ["warning", "Warning", "WARN"], default=0)
    info = _from_many(alerts, ["info", "Info", "INFORMATIONAL"], default=0)

    return {
        "ts": ts,
        "health_status": status_str,
        "health_score": health_score,
        "availability": _to_float_or_none(availability),
        "p95_latency_ms": _to_float_or_none(latency),
        "alerts_critical": int(critical or 0),
        "alerts_warning": int(warning or 0),
        "alerts_info": int(info or 0),
    }


def _from_many(d: Dict[str, Any], keys: list[str], default=None):
    for k in keys:
        if k in d:
            return d[k]
    return default


def _nested_lookup(doc: Dict[str, Any], paths: list[Tuple[str, str]]):
    for a, b in paths:
        if a in doc and isinstance(doc[a], dict) and b in doc[a]:
            return doc[a][b]
    return None


def _to_float_or_none(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


# --- SQLite sink ---

def ensure_sqlite(conn: sqlite3.Connection, table: str = DEFAULT_TABLE):
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            health_status TEXT,
            health_score REAL,
            availability REAL,
            p95_latency_ms REAL,
            alerts_critical INTEGER,
            alerts_warning INTEGER,
            alerts_info INTEGER,
            source_file TEXT
        )
        """
    )
    conn.commit()


def insert_sqlite(conn: sqlite3.Connection, row: Dict[str, Any], source_file: str, table: str = DEFAULT_TABLE):
    cols = (
        "ts, health_status, health_score, availability, p95_latency_ms, "
        "alerts_critical, alerts_warning, alerts_info, source_file"
    )
    conn.execute(
        f"INSERT INTO {table} ({cols}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            row.get("ts"),
            row.get("health_status"),
            row.get("health_score"),
            row.get("availability"),
            row.get("p95_latency_ms"),
            row.get("alerts_critical"),
            row.get("alerts_warning"),
            row.get("alerts_info"),
            source_file,
        ),
    )
    conn.commit()


# --- InfluxDB sink (optional, lazy) ---

def maybe_write_influx(args, row: Dict[str, Any]):
    if not (args.influx_url and args.influx_org and args.influx_bucket):
        return
    token = args.influx_token or os.environ.get("INFLUXDB_TOKEN")
    if not token:
        print("[influx] token missing; skip write")
        return
    try:
        from influxdb_client import InfluxDBClient, Point  # type: ignore[import-not-found]
    except Exception as e:
        print(f"[influx] influxdb-client not installed: {e}")
        return

    try:
        with InfluxDBClient(url=args.influx_url, token=token, org=args.influx_org, timeout=10_000) as client:
            write_api = client.write_api()
            p = (
                Point("agi_metrics")
                .time(row["ts"])  # ISO 8601
                .tag("source", "collector")
                .field("health_score", float(row["health_score"]) if row["health_score"] is not None else 0.0)
                .field("availability", float(row["availability"]) if row["availability"] is not None else 0.0)
                .field("p95_latency_ms", float(row["p95_latency_ms"]) if row["p95_latency_ms"] is not None else 0.0)
                .field("alerts_critical", int(row["alerts_critical"]))
                .field("alerts_warning", int(row["alerts_warning"]))
                .field("alerts_info", int(row["alerts_info"]))
            )
            write_api.write(bucket=args.influx_bucket, org=args.influx_org, record=p)
    except Exception as e:
        print(f"[influx] write failed: {e}")


def collect_once(args) -> bool:
    src = None
    if args.source == "report":
        src = os.path.join(OUTPUTS_DIR, "monitoring_metrics_latest.json")
    elif args.source == "quick":
        src = os.path.join(OUTPUTS_DIR, "quick_status_latest.json")
    else:
        src = find_latest_source()

    if not src or not os.path.isfile(src):
        print("[collector] no source JSON found; run monitoring tasks to generate metrics")
        return False

    try:
        doc = load_metrics_json(src)
    except Exception as e:
        print(f"[collector] failed to parse {src}: {e}")
        return False

    row = extract_fields(doc)

    # SQLite
    os.makedirs(os.path.dirname(args.sqlite), exist_ok=True)
    with sqlite3.connect(args.sqlite) as conn:
        ensure_sqlite(conn, args.table)
        insert_sqlite(conn, row, src, args.table)

    # Influx (optional)
    maybe_write_influx(args, row)

    print(
        f"[collector] captured ts={row['ts']} health={row['health_status']} "
        f"avail={row['availability']} p95ms={row['p95_latency_ms']} from={os.path.basename(src)}"
    )
    return True


essential_description = (
    "Collect monitoring metrics periodically and store in SQLite. "
    "Use --once for one-shot, or --interval for daemon-like collection."
)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=essential_description)
    p.add_argument("--interval", type=int, default=60, help="collection interval in seconds")
    p.add_argument("--once", action="store_true", help="run one-shot and exit")
    p.add_argument("--source", choices=["auto", "report", "quick"], default="auto", help="metrics source preference")

    # SQLite
    p.add_argument("--sqlite", default=DEFAULT_SQLITE_PATH, help="sqlite database path")
    p.add_argument("--table", default=DEFAULT_TABLE, help="sqlite table name")

    # InfluxDB (optional)
    p.add_argument("--influx-url", default=None)
    p.add_argument("--influx-org", default=None)
    p.add_argument("--influx-bucket", default=None)
    p.add_argument("--influx-token", default=None)

    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    _setup_signals()

    if args.once:
        ok = collect_once(args)
        return 0 if ok else 2

    # loop
    print(
        f"[collector] starting interval={args.interval}s source={args.source} sqlite={args.sqlite} table={args.table}"
    )
    while not STOP_REQUESTED:
        try:
            collect_once(args)
        except Exception as e:
            print(f"[collector] unhandled error: {e}")
        # sleep with early-exit support
        for _ in range(max(1, args.interval)):
            if STOP_REQUESTED:
                break
            time.sleep(1)

    print("[collector] stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
