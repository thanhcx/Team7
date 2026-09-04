"""Server metrics tool for the I&O Operations Support Agent.

Reads ``data/server_metrics.csv`` deterministically and returns
structured Python data.  No LLM is used.

CSV schema (discovered from the actual file):
    timestamp, hostname, cpu_pct, memory_pct, filesystem_pct,
    load_avg_5m, swap_pct
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


SERVER_METRICS_FILE = DATA_DIR / "server_metrics.csv"

_NUMERIC_FIELDS = {
    "cpu_pct": float,
    "memory_pct": float,
    "filesystem_pct": float,
    "load_avg_5m": float,
    "swap_pct": float,
}


def get_server_metrics(
    hostname: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve server metrics with optional filtering.

    Parameters
    ----------
    hostname
        Filter by ``hostname`` (case-insensitive substring match).
        Typical values: ``APP01``, ``APP02``.
    start_time
        Start of the analysis window (inclusive).
    end_time
        End of the analysis window (inclusive).

    Returns
    -------
    list[dict]
        Matching metric rows with numeric values converted to ``float``.

    Raises
    ------
    FileNotFoundError
        If the metrics file is missing.
    ValueError
        If the time window is invalid.
    """
    start_dt, end_dt = validate_time_window(start_time, end_time)

    rows = read_csv(SERVER_METRICS_FILE, _NUMERIC_FIELDS)

    if hostname:
        rows = [r for r in rows if case_insensitive_match(r.get("hostname"), hostname)]

    rows = filter_by_time_window(rows, "timestamp", start_dt, end_dt)

    return rows


if __name__ == "__main__":
    import json

    data = get_server_metrics(
        hostname="APP01",
        start_time="2026-08-25 14:00",
        end_time="2026-08-25 14:15",
    )
    print(json.dumps(data, indent=2))