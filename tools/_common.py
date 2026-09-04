"""Shared utilities for the I&O Operations Support Agent data tool layer.

This module provides common helpers used by all deterministic data tools:
- timestamp parsing
- time-window validation and filtering
- CSV reading with numeric type conversion
- file-existence checks

No LLM is used.  Everything is deterministic and READ-ONLY.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------

#: Accepted timestamp formats (most specific first).
_TIMESTAMP_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
)


def parse_timestamp(value: str) -> datetime:
    """Parse a timestamp string into a :class:`datetime`.

    Supported formats:
        - ``YYYY-MM-DD HH:MM:SS``
        - ``YYYY-MM-DD HH:MM``
        - ``YYYY-MM-DDTHH:MM:SS``
        - ``YYYY-MM-DDTHH:MM``

    Raises
    ------
    ValueError
        If *value* does not match any accepted format.
    """
    if not value or not isinstance(value, str):
        raise ValueError(f"Invalid timestamp value: {value!r}")

    stripped = value.strip()
    for fmt in _TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(stripped, fmt)
        except ValueError:
            continue

    raise ValueError(
        f"Timestamp {value!r} does not match any accepted format: "
        f"{', '.join(_TIMESTAMP_FORMATS)}"
    )


def validate_time_window(
    start_time: str | None, end_time: str | None
) -> tuple[datetime | None, datetime | None]:
    """Validate and parse an optional time window.

    Returns a ``(start, end)`` tuple of :class:`datetime` objects (or
    ``None`` when a bound is not supplied).

    Raises
    ------
    ValueError
        If *start_time* is after *end_time* (invalid range) or if either
        value cannot be parsed.
    """
    start_dt = parse_timestamp(start_time) if start_time else None
    end_dt = parse_timestamp(end_time) if end_time else None

    if start_dt and end_dt and start_dt > end_dt:
        raise ValueError(
            f"Invalid time range: start ({start_time}) is after end ({end_time})"
        )

    return start_dt, end_dt


def is_within_window(
    ts: datetime, start: datetime | None, end: datetime | None
) -> bool:
    """Return ``True`` when *ts* falls inside the ``[start, end]`` window.

    Unspecified bounds are treated as open-ended.
    """
    if start and ts < start:
        return False
    if end and ts > end:
        return False
    return True


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def read_csv(
    file_path: Path,
    numeric_fields: dict[str, Callable[[str], Any]] | None = None,
) -> list[dict[str, Any]]:
    """Read a CSV file into a list of dicts.

    Parameters
    ----------
    file_path
        Path to the CSV file.
    numeric_fields
        Mapping of column name -> conversion function (``int`` or ``float``).
        Matching columns are converted; all other columns remain strings.

    Raises
    ------
    FileNotFoundError
        If *file_path* does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    rows: list[dict[str, Any]] = []
    numeric_fields = numeric_fields or {}

    with file_path.open(mode="r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            converted: dict[str, Any] = {}
            for key, value in row.items():
                converter = numeric_fields.get(key)
                if converter is not None and value is not None and value != "":
                    try:
                        converted[key] = converter(value)
                    except (ValueError, TypeError):
                        converted[key] = value
                else:
                    converted[key] = value
            rows.append(converted)

    return rows


def filter_by_time_window(
    rows: list[dict[str, Any]],
    timestamp_key: str,
    start: datetime | None,
    end: datetime | None,
) -> list[dict[str, Any]]:
    """Filter *rows* whose ``timestamp_key`` value falls within ``[start, end]``.

    The timestamp column is expected to be a string parseable by
    :func:`parse_timestamp`.
    """
    if start is None and end is None:
        return rows

    result: list[dict[str, Any]] = []
    for row in rows:
        raw_ts = row.get(timestamp_key)
        if not raw_ts:
            continue
        try:
            ts = parse_timestamp(str(raw_ts))
        except ValueError:
            continue
        if is_within_window(ts, start, end):
            result.append(row)

    return result


def case_insensitive_match(value: str | None, target: str) -> bool:
    """Return ``True`` when *target* is a case-insensitive substring of *value*."""
    if not value:
        return False
    return target.lower() in value.lower()