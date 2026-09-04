"""Application log search tool for the I&O Operations Support Agent.

Reads ``data/application.log`` deterministically and returns structured
Python data.  No LLM is used.

Log line format (discovered from the actual file)::

    YYYY-MM-DD HH:MM:SS LEVEL  [application] message

Examples::

    2026-08-25 13:50:11 INFO  [internet-banking] Health check OK
    2026-08-25 14:07:41 ERROR [internet-banking] Unable to acquire database connection within 3000 ms
"""

from __future__ import annotations

import re
from typing import Any

from ._common import (
    DATA_DIR,
    is_within_window,
    parse_timestamp,
    validate_time_window,
)


APPLICATION_LOG_FILE = DATA_DIR / "application.log"

# Regex matching: timestamp  LEVEL  [application]  message
# Level is a word (INFO/WARN/ERROR/etc.), application is inside square brackets.
_LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>\w+)\s+"
    r"\[(?P<application>[^\]]+)\]\s+"
    r"(?P<message>.*)$"
)


def _parse_log_line(line: str) -> dict[str, Any] | None:
    """Parse a single log line into a structured dict.

    Returns ``None`` if the line does not match the expected format.
    """
    match = _LOG_PATTERN.match(line.strip())
    if not match:
        return None

    return {
        "timestamp": match.group("timestamp"),
        "level": match.group("level"),
        "application": match.group("application"),
        "message": match.group("message"),
        "raw": line.rstrip("\n"),
    }


def search_application_logs(
    keyword: str | None = None,
    level: str | None = None,
    application: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> list[dict[str, Any]]:
    """Search application logs with optional filtering.

    Parameters
    ----------
    keyword
        Case-insensitive keyword searched within the log ``message``
        (and ``raw`` line).  When ``None``, no keyword filter is applied.
    level
        Filter by log ``level`` (case-insensitive exact match).
        Typical values: ``INFO``, ``WARN``, ``ERROR``.
    application
        Filter by ``application`` name inside the square brackets
        (case-insensitive substring match).
        Typical value: ``internet-banking``.
    start_time
        Start of the analysis window (inclusive).
        Accepted formats: ``YYYY-MM-DD HH:MM`` or ``YYYY-MM-DD HH:MM:SS``.
    end_time
        End of the analysis window (inclusive).

    Returns
    -------
    list[dict]
        Each dict has keys: ``timestamp``, ``level``, ``application``,
        ``message``, ``raw``.

    Raises
    ------
    FileNotFoundError
        If the log file is missing.
    ValueError
        If the time window is invalid.
    """
    if not APPLICATION_LOG_FILE.exists():
        raise FileNotFoundError(f"Log file not found: {APPLICATION_LOG_FILE}")

    start_dt, end_dt = validate_time_window(start_time, end_time)

    results: list[dict[str, Any]] = []

    with APPLICATION_LOG_FILE.open(mode="r", encoding="utf-8-sig") as fh:
        for line in fh:
            parsed = _parse_log_line(line)
            if parsed is None:
                # Skip lines that do not match the expected log format.
                continue

            # --- level filter ------------------------------------------------
            if level and parsed["level"].upper() != level.upper():
                continue

            # --- application filter -----------------------------------------
            if application and application.lower() not in parsed["application"].lower():
                continue

            # --- keyword filter ---------------------------------------------
            if keyword:
                haystack = (parsed["message"] + " " + parsed["raw"]).lower()
                if keyword.lower() not in haystack:
                    continue

            # --- time window ------------------------------------------------
            try:
                ts = parse_timestamp(parsed["timestamp"])
            except ValueError:
                continue

            if not is_within_window(ts, start_dt, end_dt):
                continue

            results.append(parsed)

    return results


if __name__ == "__main__":
    import json

    data = search_application_logs(
        level="ERROR",
        start_time="2026-08-25 14:00",
        end_time="2026-08-25 14:15",
    )
    print(json.dumps(data, indent=2))