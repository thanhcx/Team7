"""Application metrics tool for the I&O Operations Support Agent.

Reads ``data/application_metrics.csv`` deterministically and returns
structured Python data.  No LLM is used.

CSV schema (discovered from the actual file):
    timestamp, system_id, application, response_time_ms, error_rate_pct,
    db_connection_pool_pct, thread_pool_pct, request_rate_rps
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


APPLICATION_METRICS_FILE = DATA_DIR / "application_metrics.csv"

_NUMERIC_FIELDS = {
    "response_time_ms": int,
    "error_rate_pct": float,
    "db_connection_pool_pct": float,
    "thread_pool_pct": float,
    "request_rate_rps": int,
}


def get_application_metrics(
    system_id: str | None = None,
    application: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve application metrics with optional filtering.

    Parameters
    ----------
    system_id
        Filter by ``system_id`` (case-insensitive exact match).
    application
        Filter by ``application`` name (case-insensitive substring match).
    start_time
        Start of the analysis window (inclusive).  Accepted formats:
        ``YYYY-MM-DD HH:MM`` or ``YYYY-MM-DD HH:MM:SS``.
    end_time
        End of the analysis window (inclusive).

    Returns
    -------
    list[dict]
        Matching metric rows with numeric values converted to ``int``/``float``.

    Raises
    ------
    FileNotFoundError
        If the metrics file is missing.
    ValueError
        If the time window is invalid.
    """
    start_dt, end_dt = validate_time_window(start_time, end_time)

    rows = read_csv(APPLICATION_METRICS_FILE, _NUMERIC_FIELDS)

    # --- component / system filters -------------------------------------
    if system_id:
        rows = [r for r in rows if case_insensitive_match(r.get("system_id"), system_id)]

    if application:
        rows = [
            r for r in rows if case_insensitive_match(r.get("application"), application)
        ]

    # --- time window ----------------------------------------------------
    rows = filter_by_time_window(rows, "timestamp", start_dt, end_dt)

    return rows


if __name__ == "__main__":
    import json

    data = get_application_metrics(
        system_id="SYS-IB-001",
        start_time="2026-08-25 14:00",
        end_time="2026-08-25 14:15",
    )
    print(json.dumps(data, indent=2))