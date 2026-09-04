"""Tests for ``tools/vmware_metrics.py``."""

from __future__ import annotations

import pytest

from tools.vmware_metrics import get_vmware_metrics


class TestGetVmwareMetrics:
    def test_no_filters_returns_all_rows(self):
        rows = get_vmware_metrics()
        # 32 data rows (2 VMs × 16 timestamps).
        assert len(rows) == 32

    def test_filter_by_cluster(self):
        rows = get_vmware_metrics(cluster="CLUSTER-DIGITAL")
        assert len(rows) == 32

    def test_filter_by_vm_name(self):
        rows = get_vmware_metrics(vm_name="vm-app01")
        assert len(rows) == 16
        assert all(r["vm_name"] == "vm-app01" for r in rows)

    def test_filter_by_esxi_host(self):
        rows = get_vmware_metrics(esxi_host="esxi-05")
        assert len(rows) == 16
        assert all(r["esxi_host"] == "esxi-05" for r in rows)

    def test_combined_filters(self):
        rows = get_vmware_metrics(
            cluster="CLUSTER-DIGITAL",
            vm_name="vm-app02",
            esxi_host="esxi-06",
        )
        assert len(rows) == 16

    def test_time_window(self):
        rows = get_vmware_metrics(
            vm_name="vm-app01",
            start_time="2026-08-25 14:00",
            end_time="2026-08-25 14:10",
        )
        assert len(rows) == 3

    def test_numeric_types_converted(self):
        rows = get_vmware_metrics(
            vm_name="vm-app01",
            start_time="2026-08-25 14:10",
            end_time="2026-08-25 14:10",
        )
        row = rows[0]
        assert isinstance(row["cpu_ready_pct"], float)
        assert isinstance(row["memory_balloon_mb"], int)
        assert isinstance(row["host_cpu_pct"], float)
        assert isinstance(row["host_memory_pct"], float)

    def test_expected_keys(self):
        rows = get_vmware_metrics()
        expected_keys = {
            "timestamp", "cluster", "vm_name", "esxi_host",
            "cpu_ready_pct", "memory_balloon_mb",
            "host_cpu_pct", "host_memory_pct",
        }
        assert set(rows[0].keys()) == expected_keys

    def test_no_match(self):
        rows = get_vmware_metrics(vm_name="nonexistent")
        assert rows == []

    def test_invalid_time_window_raises(self):
        with pytest.raises(ValueError):
            get_vmware_metrics(
                start_time="2026-08-25 14:30",
                end_time="2026-08-25 14:00",
            )

    def test_cpu_ready_is_low(self):
        """In the data, cpu_ready_pct is consistently ~2.1 / 1.8 (no VM contention)."""
        rows = get_vmware_metrics(vm_name="vm-app01")
        for row in rows:
            assert row["cpu_ready_pct"] < 5.0

    def test_no_memory_ballooning(self):
        """memory_balloon_mb is 0 throughout (no VM memory pressure)."""
        rows = get_vmware_metrics()
        for row in rows:
            assert row["memory_balloon_mb"] == 0