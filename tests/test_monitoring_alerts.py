"""Tests for ``tools/monitoring_alerts.py``."""

from __future__ import annotations

import pytest

from tools.monitoring_alerts import get_monitoring_alerts


class TestGetMonitoringAlerts:
    def test_no_filters_returns_all_alerts(self):
        rows = get_monitoring_alerts()
        # 6 alert rows in the file.
        assert len(rows) == 6

    def test_filter_by_system_id(self):
        rows = get_monitoring_alerts(system_id="SYS-IB-001")
        assert len(rows) == 6

    def test_filter_by_domain_application(self):
        rows = get_monitoring_alerts(domain="Application")
        # ALT-1001, ALT-1002, ALT-1003, ALT-2003 = 4
        assert len(rows) == 4

    def test_filter_by_domain_storage(self):
        rows = get_monitoring_alerts(domain="Storage")
        # ALT-2001, ALT-2002 = 2
        assert len(rows) == 2

    def test_filter_by_severity_critical(self):
        rows = get_monitoring_alerts(severity="CRITICAL")
        # ALT-1002, ALT-1003, ALT-2002, ALT-2003 = 4
        assert len(rows) == 4

    def test_filter_by_severity_warning(self):
        rows = get_monitoring_alerts(severity="WARNING")
        # ALT-1001, ALT-2001 = 2
        assert len(rows) == 2

    def test_filter_by_status_open(self):
        rows = get_monitoring_alerts(status="OPEN")
        assert len(rows) == 6

    def test_filter_by_component(self):
        rows = get_monitoring_alerts(component="internet-banking")
        assert len(rows) == 4

    def test_time_window_scenario1(self):
        rows = get_monitoring_alerts(
            start_time="2026-08-25 14:00",
            end_time="2026-08-25 14:15",
        )
        # ALT-1001 (14:05), ALT-1002 (14:10), ALT-1003 (14:10) = 3
        assert len(rows) == 3

    def test_time_window_scenario2(self):
        rows = get_monitoring_alerts(
            start_time="2026-08-26 10:00",
            end_time="2026-08-26 10:15",
        )
        # ALT-2001 (10:00), ALT-2002 (10:05), ALT-2003 (10:10) = 3
        assert len(rows) == 3

    def test_expected_keys(self):
        rows = get_monitoring_alerts()
        expected_keys = {
            "alert_id", "timestamp", "system_id", "domain",
            "component", "severity", "alert_code",
            "description", "status",
        }
        assert set(rows[0].keys()) == expected_keys

    def test_all_alerts_are_open(self):
        rows = get_monitoring_alerts()
        assert all(r["status"] == "OPEN" for r in rows)

    def test_no_match(self):
        rows = get_monitoring_alerts(system_id="NOPE")
        assert rows == []

    def test_invalid_time_window_raises(self):
        with pytest.raises(ValueError):
            get_monitoring_alerts(
                start_time="2026-08-26 10:30",
                end_time="2026-08-26 10:00",
            )

    def test_alert_ids_unique(self):
        rows = get_monitoring_alerts()
        alert_ids = [r["alert_id"] for r in rows]
        assert len(alert_ids) == len(set(alert_ids))