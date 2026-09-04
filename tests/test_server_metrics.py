"""Tests for ``tools/server_metrics.py``."""

from __future__ import annotations

import pytest

from tools.server_metrics import get_server_metrics


class TestGetServerMetrics:
    def test_no_filters_returns_all_rows(self):
        rows = get_server_metrics()
        # 32 data rows (2 hosts × 16 timestamps).
        assert len(rows) == 32

    def test_filter_by_hostname_app01(self):
        rows = get_server_metrics(hostname="APP01")
        assert len(rows) == 16
        assert all(r["hostname"] == "APP01" for r in rows)

    def test_filter_by_hostname_app02(self):
        rows = get_server_metrics(hostname="APP02")
        assert len(rows) == 16
        assert all(r["hostname"] == "APP02" for r in rows)

    def test_hostname_case_insensitive(self):
        rows = get_server_metrics(hostname="app01")
        assert len(rows) == 16

    def test_time_window(self):
        rows = get_server_metrics(
            hostname="APP01",
            start_time="2026-08-25 14:00",
            end_time="2026-08-25 14:10",
        )
        # 14:00, 14:05, 14:10 = 3 rows
        assert len(rows) == 3

    def test_numeric_types_converted(self):
        rows = get_server_metrics(
            hostname="APP01",
            start_time="2026-08-25 14:10",
            end_time="2026-08-25 14:10",
        )
        row = rows[0]
        assert isinstance(row["cpu_pct"], float)
        assert isinstance(row["memory_pct"], float)
        assert isinstance(row["filesystem_pct"], float)
        assert isinstance(row["load_avg_5m"], float)
        assert isinstance(row["swap_pct"], float)

    def test_expected_keys(self):
        rows = get_server_metrics()
        expected_keys = {
            "timestamp", "hostname", "cpu_pct", "memory_pct",
            "filesystem_pct", "load_avg_5m", "swap_pct",
        }
        assert set(rows[0].keys()) == expected_keys

    def test_no_matching_hostname(self):
        rows = get_server_metrics(hostname="NOPE")
        assert rows == []

    def test_invalid_time_window_raises(self):
        with pytest.raises(ValueError):
            get_server_metrics(
                start_time="2026-08-25 14:30",
                end_time="2026-08-25 14:00",
            )

    def test_cpu_values_in_expected_range(self):
        """All CPU values should be reasonable percentages (0–100)."""
        rows = get_server_metrics()
        for row in rows:
            assert 0 <= row["cpu_pct"] <= 100
            assert 0 <= row["memory_pct"] <= 100