"""Network metrics tool for the I&O Operations Support Agent.

Reads ``data/network_metrics.csv`` deterministically and returns
structured Python data.  No LLM is used.

CSV schema (discovered from the actual file):
    timestamp, network_zone, device, endpoint, latency_ms,
    packet_loss_pct, interface_error_pct, link_utilization_pct
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


NETWORK_METRICS_FILE = DATA_DIR / "network_metrics.csv"

_NUMERIC_FIELDS = {
    "latency_ms": float,
    "packet_loss_pct": float,
    "interface_error_pct": float,
    "link_utilization_pct": float,
}


def get_network_metrics(
    network_zone: str | None = None,
    device: str | None = None,
    endpoint: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve network metrics with optional filtering.

    Parameters
    ----------
    network_zone
        Filter by ``network_zone`` (case-insensitive substring match).
        Typical value: ``APP-ZONE``.
    device
        Filter by ``device`` (case-insensitive substring match).
        Typical values: ``leaf-101``, ``leaf-102``.
    endpoint
        Filter by ``endpoint`` (case-insensitive substring match).
        Typical values: ``APP01``, ``APP02``.
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

    rows = read_csv(NETWORK_METRICS_FILE, _NUMERIC_FIELDS)

    if network_zone:
        rows = [
            r for r in rows if case_insensitive_match(r.get("network_zone"), network_zone)
        ]

    if device:
        rows = [r for r in rows if case_insensitive_match(r.get("device"), device)]

    if endpoint:
        rows = [r for r in rows if case_insensitive_match(r.get("endpoint"), endpoint)]

    rows = filter_by_time_window(rows, "timestamp", start_dt, end_dt)

    return rows


if __name__ == "__main__":
    import json

    data = get_network_metrics(
        endpoint="APP01",
        start_time="2026-08-25 14:00",
        end_time="2026-08-25 14:15",
    )
    print(json.dumps(data, indent=2))