"""Tests for the shared utilities in ``tools/_common.py``."""

from __future__ import annotations

from datetime import datetime

import pytest

from tools._common import (
    case_insensitive_match,
    filter_by_time_window,
    is_within_window,
    parse_timestamp,
    read_csv,
    validate_time_window,
)


# ---------------------------------------------------------------------------
# parse_timestamp
# ---------------------------------------------------------------------------

class TestParseTimestamp:
    def test_full_timestamp_with_seconds(self):
        assert parse_timestamp("2026-08-25 14:05:18") == datetime(2026, 8, 25, 14, 5, 18)

    def test_timestamp_without_seconds(self):
        assert parse_timestamp("2026-08-25 14:05") == datetime(2026, 8, 25, 14, 5)

    def test_iso_timestamp_with_seconds(self):
        assert parse_timestamp("2026-08-25T14:05:18") == datetime(2026, 8, 25, 14, 5, 18)

    def test_iso_timestamp_without_seconds(self):
        assert parse_timestamp("2026-08-25T14:05") == datetime(2026, 8, 25, 14, 5)

    def test_strips_whitespace(self):
        assert parse_timestamp("  2026-08-25 14:05  ") == datetime(2026, 8, 25, 14, 5)

    @pytest.mark.parametrize("bad", ["", None, "not-a-date", "2026/08/25 14:05", "25-08-2026 14:05"])
    def test_invalid_raises(self, bad):
        with pytest.raises(ValueError):
            parse_timestamp(bad)


# ---------------------------------------------------------------------------
# validate_time_window
# ---------------------------------------------------------------------------

class TestValidateTimeWindow:
    def test_both_none(self):
        assert validate_time_window(None, None) == (None, None)

    def test_start_only(self):
        start, end = validate_time_window("2026-08-25 14:00", None)
        assert start == datetime(2026, 8, 25, 14, 0)
        assert end is None

    def test_end_only(self):
        start, end = validate_time_window(None, "2026-08-25 14:00")
        assert start is None
        assert end == datetime(2026, 8, 25, 14, 0)

    def test_valid_range(self):
        start, end = validate_time_window("2026-08-25 14:00", "2026-08-25 14:30")
        assert start < end

    def test_start_after_end_raises(self):
        with pytest.raises(ValueError, match="Invalid time range"):
            validate_time_window("2026-08-25 14:30", "2026-08-25 14:00")

    def test_invalid_start_raises(self):
        with pytest.raises(ValueError):
            validate_time_window("bad", "2026-08-25 14:00")


# ---------------------------------------------------------------------------
# is_within_window
# ---------------------------------------------------------------------------

class TestIsWithinWindow:
    ts = datetime(2026, 8, 25, 14, 10)

    def test_no_bounds(self):
        assert is_within_window(self.ts, None, None) is True

    def test_within(self):
        start = datetime(2026, 8, 25, 14, 0)
        end = datetime(2026, 8, 25, 14, 20)
        assert is_within_window(self.ts, start, end) is True

    def test_before_start(self):
        start = datetime(2026, 8, 25, 14, 15)
        assert is_within_window(self.ts, start, None) is False

    def test_after_end(self):
        end = datetime(2026, 8, 25, 14, 5)
        assert is_within_window(self.ts, None, end) is False

    def test_on_boundary_start(self):
        start = self.ts
        assert is_within_window(self.ts, start, None) is True

    def test_on_boundary_end(self):
        end = self.ts
        assert is_within_window(self.ts, None, end) is True


# ---------------------------------------------------------------------------
# case_insensitive_match
# ---------------------------------------------------------------------------

class TestCaseInsensitiveMatch:
    def test_exact(self):
        assert case_insensitive_match("APP01", "APP01") is True

    def test_case_diff(self):
        assert case_insensitive_match("app01", "APP01") is True

    def test_substring(self):
        assert case_insensitive_match("vm-app01", "app01") is True

    def test_no_match(self):
        assert case_insensitive_match("APP02", "APP01") is False

    def test_none_value(self):
        assert case_insensitive_match(None, "APP01") is False

    def test_empty_value(self):
        assert case_insensitive_match("", "APP01") is False


# ---------------------------------------------------------------------------
# read_csv
# ---------------------------------------------------------------------------

class TestReadCsv:
    def test_reads_system_inventory(self, tmp_path):
        csv_content = "system_id,system_name\nSYS-IB-001,Internet Banking\n"
        f = tmp_path / "test.csv"
        f.write_text(csv_content, encoding="utf-8")
        rows = read_csv(f)
        assert len(rows) == 1
        assert rows[0]["system_id"] == "SYS-IB-001"

    def test_numeric_conversion(self, tmp_path):
        csv_content = "ts,val\n2026-08-25 14:00,42\n"
        f = tmp_path / "test.csv"
        f.write_text(csv_content, encoding="utf-8")
        rows = read_csv(f, {"val": int})
        assert rows[0]["val"] == 42
        assert isinstance(rows[0]["val"], int)

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            read_csv(__import__("pathlib").Path("nonexistent_file.csv"))


# ---------------------------------------------------------------------------
# filter_by_time_window
# ---------------------------------------------------------------------------

class TestFilterByTimeWindow:
    rows = [
        {"timestamp": "2026-08-25 13:50"},
        {"timestamp": "2026-08-25 14:05"},
        {"timestamp": "2026-08-25 14:15"},
        {"timestamp": "2026-08-25 14:25"},
    ]

    def test_no_filter(self):
        assert len(filter_by_time_window(self.rows, "timestamp", None, None)) == 4

    def test_start_only(self):
        start = datetime(2026, 8, 25, 14, 0)
        result = filter_by_time_window(self.rows, "timestamp", start, None)
        assert len(result) == 3

    def test_end_only(self):
        end = datetime(2026, 8, 25, 14, 15)
        result = filter_by_time_window(self.rows, "timestamp", None, end)
        assert len(result) == 3

    def test_both_bounds(self):
        start = datetime(2026, 8, 25, 14, 0)
        end = datetime(2026, 8, 25, 14, 15)
        result = filter_by_time_window(self.rows, "timestamp", start, end)
        assert len(result) == 2