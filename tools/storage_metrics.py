"""Storage metrics tool for the I&O Operations Support Agent.

Reads ``data/storage_metrics.csv`` deterministically and returns
structured Python data.  No LLM is used.

CSV schema (discovered from the actual file):
    timestamp, storage_pool, datastore, latency_ms, iops,
    throughput_mbps, queue_depth_avg, capacity_used_pct
"""

from __future__ import annotations

from typing import Any

from ._common import (
    DATA_DIR,
    case_insensitive_match,
    filter_by_time_window,
    read_csv,
    validate_time_window,
)


STORAGE_METRICS_FILE = DATA_DIR / "storage_metrics.csv"

_NUMERIC_FIELDS = {
    "latency_ms": float,
    "iops": int,
    "throughput_mbps": int,
    "queue_depth_avg": float,
    "capacity_used_pct": float,
}


def get_storage_metrics(
    storage_pool: str | None = None,
    datastore: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve storage metrics with optional filtering.

    Parameters
    ----------
    storage_pool
        Filter by ``storage_pool`` (case-insensitive substring match).
        Typical value: ``POOL-FLASH-01``.
    datastore
        Filter by ``datastore`` (case-insensitive substring match).
        Typical value: ``DS-IB-01``.
    start_time
        Start of the analysis window (inclusive).
    end_time
        End of the analysis window (inclusive).

    Returns
    -------
    list[dict]
        Matching metric rows with numeric values converted.

    Raises
    ------
    FileNotFoundError
        If the metrics file is missing.
    ValueError
        If the time window is invalid.
    """
    start_dt, end_dt = validate_time_window(start_time, end_time)

    rows = read_csv(STORAGE_METRICS_FILE, _NUMERIC_FIELDS)

    if storage_pool:
        rows = [
            r for r in rows if case_insensitive_match(r.get("storage_pool"), storage_pool)
        ]

    if datastore:
        rows = [
            r for r in rows if case_insensitive_match(r.get("datastore"), datastore)
        ]

    rows = filter_by_time_window(rows, "timestamp", start_dt, end_dt)

    return rows


if __name__ == "__main__":
    import json

    data = get_storage_metrics(
        storage_pool="POOL-FLASH-01",
        start_time="2026-08-26 10:00",
        end_time="2026-08-26 10:15",
    )
    print(json.dumps(data, indent=2))