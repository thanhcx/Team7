"""Tests for ``tools/storage_metrics.py``."""

from __future__ import annotations

import pytest

from tools.storage_metrics import get_storage_metrics


class TestGetStorageMetrics:
    def test_no_filters_returns_all_rows(self):
        rows = get_storage_metrics()
        # 16 data rows.
        assert len(rows) == 16

    def test_filter_by_storage_pool(self):
        rows = get_storage_metrics(storage_pool="POOL-FLASH-01")
        assert len(rows) == 16

    def test_filter_by_datastore(self):
        rows = get_storage_metrics(datastore="DS-IB-01")
        assert len(rows) == 16

    def test_combined_filters(self):
        rows = get_storage_metrics(
            storage_pool="POOL-FLASH-01",
            datastore="DS-IB-01",
        )
        assert len(rows) == 16

    def test_time_window_scenario2(self):
        """Scenario 2 storage latency spike on 2026-08-26 10:00–10:20."""
        rows = get_storage_metrics(
            storage_pool="POOL-FLASH-01",
            start_time="2026-08-26 10:00",
            end_time="2026-08-26 10:20",
        )
        # 10:00, 10:05, 10:10, 10:15, 10:20 = 5 rows
        assert len(rows) == 5

    def test_numeric_types_converted(self):
        rows = get_storage_metrics(
            start_time="2026-08-26 10:10",
            end_time="2026-08-26 10:10",
        )
        row = rows[0]
        assert isinstance(row["latency_ms"], float)
        assert isinstance(row["iops"], int)
        assert isinstance(row["throughput_mbps"], int)
        assert isinstance(row["queue_depth_avg"], float)
        assert isinstance(row["capacity_used_pct"], float)

    def test_expected_keys(self):
        rows = get_storage_metrics()
        expected_keys = {
            "timestamp", "storage_pool", "datastore",
            "latency_ms", "iops", "throughput_mbps",
            "queue_depth_avg", "capacity_used_pct",
        }
        assert set(rows[0].keys()) == expected_keys

    def test_no_match(self):
        rows = get_storage_metrics(storage_pool="NOPE")
        assert rows == []

    def test_invalid_time_window_raises(self):
        with pytest.raises(ValueError):
            get_storage_metrics(
                start_time="2026-08-26 10:30",
                end_time="2026-08-26 10:00",
            )

    def test_latency_spike_scenario2(self):
        """At 2026-08-26 10:10, latency_ms = 35.0 (critical)."""
        rows = get_storage_metrics(
            start_time="2026-08-26 10:10",
            end_time="2026-08-26 10:10",
        )
        assert rows[0]["latency_ms"] == 35.0

    def test_latency_normal_scenario1(self):
        """On 2026-08-25, storage latency stays low (< 5 ms)."""
        rows = get_storage_metrics(
            start_time="2026-08-25 14:00",
            end_time="2026-08-25 14:20",
        )
        for row in rows:
            assert row["latency_ms"] < 5.0