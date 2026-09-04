"""Monitoring alerts tool for the I&O Operations Support Agent.

Reads ``data/monitoring_alerts.csv`` deterministically and returns
structured Python data.  No LLM is used.

CSV schema (discovered from the actual file):
    alert_id, timestamp, system_id, domain, component, severity,
    alert_code, description, status
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


MONITORING_ALERTS_FILE = DATA_DIR / "monitoring_alerts.csv"

# No numeric fields in this file — all columns are strings.


def get_monitoring_alerts(
    system_id: str | None = None,
    domain: str | None = None,
    component: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve monitoring alerts with optional filtering.

    Parameters
    ----------
    system_id
        Filter by ``system_id`` (case-insensitive substring match).
    domain
        Filter by ``domain`` (case-insensitive substring match).
        Typical values: ``Application``, ``Storage``.
    component
        Filter by ``component`` (case-insensitive substring match).
        Typical values: ``internet-banking``, ``POOL-FLASH-01``.
    severity
        Filter by ``severity`` (case-insensitive substring match).
        Typical values: ``WARNING``, ``CRITICAL``.
    status
        Filter by ``status`` (case-insensitive substring match).
        Typical value: ``OPEN``.
    start_time
        Start of the analysis window (inclusive).
    end_time
        End of the analysis window (inclusive).

    Returns
    -------
    list[dict]
        Matching alert rows (all string values).

    Raises
    ------
    FileNotFoundError
        If the alerts file is missing.
    ValueError
        If the time window is invalid.
    """
    start_dt, end_dt = validate_time_window(start_time, end_time)

    rows = read_csv(MONITORING_ALERTS_FILE)

    if system_id:
        rows = [r for r in rows if case_insensitive_match(r.get("system_id"), system_id)]

    if domain:
        rows = [r for r in rows if case_insensitive_match(r.get("domain"), domain)]

    if component:
        rows = [r for r in rows if case_insensitive_match(r.get("component"), component)]

    if severity:
        rows = [r for r in rows if case_insensitive_match(r.get("severity"), severity)]

    if status:
        rows = [r for r in rows if case_insensitive_match(r.get("status"), status)]

    rows = filter_by_time_window(rows, "timestamp", start_dt, end_dt)

    return rows


if __name__ == "__main__":
    import json

    data = get_monitoring_alerts(
        system_id="SYS-IB-001",
        start_time="2026-08-25 14:00",
        end_time="2026-08-25 14:15",
    )
    print(json.dumps(data, indent=2))