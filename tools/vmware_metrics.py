"""VMware metrics tool for the I&O Operations Support Agent.

Reads ``data/vmware_metrics.csv`` deterministically and returns
structured Python data.  No LLM is used.

CSV schema (discovered from the actual file):
    timestamp, cluster, vm_name, esxi_host, cpu_ready_pct,
    memory_balloon_mb, host_cpu_pct, host_memory_pct
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


VMWARE_METRICS_FILE = DATA_DIR / "vmware_metrics.csv"

_NUMERIC_FIELDS = {
    "cpu_ready_pct": float,
    "memory_balloon_mb": int,
    "host_cpu_pct": float,
    "host_memory_pct": float,
}


def get_vmware_metrics(
    cluster: str | None = None,
    vm_name: str | None = None,
    esxi_host: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve VMware metrics with optional filtering.

    Parameters
    ----------
    cluster
        Filter by ``cluster`` (case-insensitive substring match).
        Typical value: ``CLUSTER-DIGITAL``.
    vm_name
        Filter by ``vm_name`` (case-insensitive substring match).
        Typical values: ``vm-app01``, ``vm-app02``.
    esxi_host
        Filter by ``esxi_host`` (case-insensitive substring match).
        Typical values: ``esxi-05``, ``esxi-06``.
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

    rows = read_csv(VMWARE_METRICS_FILE, _NUMERIC_FIELDS)

    if cluster:
        rows = [r for r in rows if case_insensitive_match(r.get("cluster"), cluster)]

    if vm_name:
        rows = [r for r in rows if case_insensitive_match(r.get("vm_name"), vm_name)]

    if esxi_host:
        rows = [r for r in rows if case_insensitive_match(r.get("esxi_host"), esxi_host)]

    rows = filter_by_time_window(rows, "timestamp", start_dt, end_dt)

    return rows


if __name__ == "__main__":
    import json

    data = get_vmware_metrics(
        vm_name="vm-app01",
        start_time="2026-08-25 14:00",
        end_time="2026-08-25 14:15",
    )
    print(json.dumps(data, indent=2))