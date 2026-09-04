"""Tests for ``tools/network_metrics.py``."""

from __future__ import annotations

import pytest

from tools.network_metrics import get_network_metrics


class TestGetNetworkMetrics:
    def test_no_filters_returns_all_rows(self):
        rows = get_network_metrics()
        # 32 data rows (2 endpoints × 16 timestamps).
        assert len(rows) == 32

    def test_filter_by_network_zone(self):
        rows = get_network_metrics(network_zone="APP-ZONE")
        assert len(rows) == 32

    def test_filter_by_device(self):
        rows = get_network_metrics(device="leaf-101")
        assert len(rows) == 16
        assert all(r["device"] == "leaf-101" for r in rows)

    def test_filter_by_endpoint(self):
        rows = get_network_metrics(endpoint="APP01")
        assert len(rows) == 16
        assert all(r["endpoint"] == "APP01" for r in rows)

    def test_combined_filters(self):
        rows = get_network_metrics(
            network_zone="APP-ZONE",
            device="leaf-102",
            endpoint="APP02",
        )
        assert len(rows) == 16

    def test_time_window(self):
        rows = get_network_metrics(
            endpoint="APP01",
            start_time="2026-08-25 14:00",
            end_time="2026-08-25 14:10",
        )
        assert len(rows) == 3

    def test_numeric_types_converted(self):
        rows = get_network_metrics(
            endpoint="APP01",
            start_time="2026-08-25 14:10",
            end_time="2026-08-25 14:10",
        )
        row = rows[0]
        assert isinstance(row["latency_ms"], float)
        assert isinstance(row["packet_loss_pct"], float)
        assert isinstance(row["interface_error_pct"], float)
        assert isinstance(row["link_utilization_pct"], float)

    def test_expected_keys(self):
        rows = get_network_metrics()
        expected_keys = {
            "timestamp", "network_zone", "device", "endpoint",
            "latency_ms", "packet_loss_pct",
            "interface_error_pct", "link_utilization_pct",
        }
        assert set(rows[0].keys()) == expected_keys

    def test_no_match(self):
        rows = get_network_metrics(endpoint="NOPE")
        assert rows == []

    def test_invalid_time_window_raises(self):
        with pytest.raises(ValueError):
            get_network_metrics(
                start_time="2026-08-25 14:30",
                end_time="2026-08-25 14:00",
            )

    def test_network_is_healthy(self):
        """Network metrics are stable throughout — no anomalies in the data."""
        rows = get_network_metrics()
        for row in rows:
            assert row["latency_ms"] < 5.0
            assert row["packet_loss_pct"] == 0.0
            assert row["link_utilization_pct"] < 80.0