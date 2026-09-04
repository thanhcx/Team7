"""Tests for ``tools/application_logs.py``."""

from __future__ import annotations

import pytest

from tools.application_logs import search_application_logs


class TestSearchApplicationLogs:
    def test_no_filters_returns_all_lines(self):
        rows = search_application_logs()
        # 16 log lines in the file.
        assert len(rows) == 16

    def test_filter_by_level_error(self):
        rows = search_application_logs(level="ERROR")
        # Lines 4, 5, 6, 7 = 4 ERROR lines
        assert len(rows) == 4
        assert all(r["level"] == "ERROR" for r in rows)

    def test_filter_by_level_warn(self):
        rows = search_application_logs(level="WARN")
        # Lines 2, 3, 8, 11, 12, 13 = 6 WARN lines
        assert len(rows) == 6

    def test_filter_by_level_info(self):
        rows = search_application_logs(level="INFO")
        # Lines 1, 9, 10, 14, 15, 16 = 6 INFO lines
        assert len(rows) == 6

    def test_level_case_insensitive(self):
        rows_lower = search_application_logs(level="error")
        rows_upper = search_application_logs(level="ERROR")
        assert len(rows_lower) == len(rows_upper) == 4

    def test_filter_by_application(self):
        rows = search_application_logs(application="internet-banking")
        assert len(rows) == 16

    def test_filter_by_keyword(self):
        rows = search_application_logs(keyword="database connection")
        # Lines 2, 3, 4, 6, 8, 9, 14 mention database connection / DB connection
        assert len(rows) >= 5

    def test_filter_by_keyword_timeout(self):
        rows = search_application_logs(keyword="timeout")
        # Lines 5, 7 contain "timeout"
        assert len(rows) == 2

    def test_time_window_scenario1(self):
        rows = search_application_logs(
            start_time="2026-08-25 14:00",
            end_time="2026-08-25 14:15",
        )
        # Lines from 14:02 to 14:15 = 6 lines
        assert len(rows) == 6

    def test_time_window_scenario2(self):
        rows = search_application_logs(
            start_time="2026-08-26 10:00",
            end_time="2026-08-26 10:20",
        )
        # Lines from 10:00:16 to 10:15:12 = 5 lines
        assert len(rows) == 5

    def test_parsed_keys(self):
        rows = search_application_logs(level="ERROR")
        expected_keys = {"timestamp", "level", "application", "message", "raw"}
        assert set(rows[0].keys()) == expected_keys

    def test_raw_line_contains_timestamp(self):
        rows = search_application_logs()
        for row in rows:
            assert row["timestamp"] in row["raw"]

    def test_combined_filters(self):
        rows = search_application_logs(
            level="ERROR",
            keyword="database",
            start_time="2026-08-25 14:00",
            end_time="2026-08-25 14:15",
        )
        # Lines 4 (14:07:41) and 6 (14:10:05) = 2
        assert len(rows) == 2

    def test_invalid_time_window_raises(self):
        with pytest.raises(ValueError):
            search_application_logs(
                start_time="2026-08-25 14:30",
                end_time="2026-08-25 14:00",
            )

    def test_no_keyword_match(self):
        rows = search_application_logs(keyword="nonexistent_keyword_xyz123")
        assert rows == []

    def test_all_lines_have_application(self):
        rows = search_application_logs()
        for row in rows:
            assert row["application"] == "internet-banking"