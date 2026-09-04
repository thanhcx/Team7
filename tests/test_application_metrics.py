"""Tests for ``tools/application_metrics.py``."""

from __future__ import annotations

import pytest

from tools.application_metrics import get_application_metrics


class TestGetApplicationMetrics:
    def test_no_filters_returns_all_rows(self):
        rows = get_application_metrics()
        # The file has 16 data rows.
        assert len(rows) == 16

    def test_filter_by_system_id(self):
        rows = get_application_metrics(system_id="SYS-IB-001")
        assert len(rows) == 16
        assert all(r["system_id"] == "SYS-IB-001" for r in rows)

    def test_filter_by_application(self):
        rows = get_application_metrics(application="internet-banking")
        assert len(rows) == 16

    def test_filter_by_application_case_insensitive(self):
        rows = get_application_metrics(application="INTERNET")
        assert len(rows) == 16

    def test_time_window_scenario1(self):
        rows = get_application_metrics(
            system_id="SYS-IB-001",
            start_time="2026-08-25 14:00",
            end_time="2026-08-25 14:15",
        )
        # 14:00, 14:05, 14:10, 14:15 = 4 rows
        assert len(rows) == 4
        timestamps = [r["timestamp"] for r in rows]
        assert "2026-08-25 14:00" in timestamps
        assert "2026-08-25 14:15" in timestamps

    def test_time_window_scenario2(self):
        rows = get_application_metrics(
            system_id="SYS-IB-001",
            start_time="2026-08-26 10:00",
            end_time="2026-08-26 10:20",
        )
        # 10:00, 10:05, 10:10, 10:15, 10:20 = 5 rows
        assert len(rows) == 5

    def test_numeric_types_converted(self):
        rows = get_application_metrics(
            start_time="2026-08-25 14:10",
            end_time="2026-08-25 14:10",
        )
        assert len(rows) == 1
        row = rows[0]
        assert isinstance(row["response_time_ms"], int)
        assert isinstance(row["error_rate_pct"], float)
        assert isinstance(row["db_connection_pool_pct"], float)
        assert isinstance(row["thread_pool_pct"], float)
        assert isinstance(row["request_rate_rps"], int)

    def test_expected_keys(self):
        rows = get_application_metrics()
        expected_keys = {
            "timestamp", "system_id", "application",
            "response_time_ms", "error_rate_pct",
            "db_connection_pool_pct", "thread_pool_pct",
            "request_rate_rps",
        }
        assert set(rows[0].keys()) == expected_keys

    def test_no_matching_system_id(self):
        rows = get_application_metrics(system_id="SYS-NOPE")
        assert rows == []

    def test_invalid_time_window_raises(self):
        with pytest.raises(ValueError):
            get_application_metrics(
                start_time="2026-08-25 14:30",
                end_time="2026-08-25 14:00",
            )

    def test_high_response_time_observed_scenario1(self):
        """Scenario 1 (2026-08-25 14:10) has response_time_ms = 1200."""
        rows = get_application_metrics(
            start_time="2026-08-25 14:10",
            end_time="2026-08-25 14:10",
        )
        assert rows[0]["response_time_ms"] == 1200

    def test_high_response_time_observed_scenario2(self):
        """Scenario 2 (2026-08-26 10:10) has response_time_ms = 1500."""
        rows = get_application_metrics(
            start_time="2026-08-26 10:10",
            end_time="2026-08-26 10:10",
        )
        assert rows[0]["response_time_ms"] == 1500