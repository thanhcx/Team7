"""Knowledge retrieval tool for the I&O Operations Support Agent.

Reads Markdown documents **only** from the ``knowledge/`` directory and
returns structured Python data.  No LLM is used.

The tool does **not** parse or interpret thresholds, diagnostic logic or
expected answers.  It returns the raw document content together with
lightweight metadata (title, status, version) extracted from the Markdown
header so that the Agent can cite knowledge sources explicitly.

Available knowledge documents (discovered at design time):
    01_application_performance_standard.md  — Application Performance Standard
    02_storage_performance_standard.md      — Storage Performance Standard
    03_application_slow_response_runbook.md — Runbook: Application Slow Response
    04_storage_high_latency_runbook.md      — Runbook: Storage High Latency

Security: the tool refuses any path that resolves outside ``knowledge/``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ._common import KNOWLEDGE_DIR


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

_TITLE_PATTERN = re.compile(r"^#\s+(?P<title>.+?)\s*$", re.MULTILINE)
_STATUS_PATTERN = re.compile(r"^Status:\s*(?P<status>.+?)\s*$", re.MULTILINE)
_VERSION_PATTERN = re.compile(r"^Version:\s*(?P<version>.+?)\s*$", re.MULTILINE)


def _extract_metadata(content: str, file_path: Path) -> dict[str, Any]:
    """Extract lightweight metadata from a Markdown document.

    Extracted fields:
        - title   : first ``# Heading``
        - status  : ``Status:`` line
        - version : ``Version:`` line
        - doc_type: ``standard`` or ``runbook`` (inferred from the title)
    """
    title_match = _TITLE_PATTERN.search(content)
    status_match = _STATUS_PATTERN.search(content)
    version_match = _VERSION_PATTERN.search(content)

    title = title_match.group("title").strip() if title_match else ""
    status = status_match.group("status").strip() if status_match else ""
    version = version_match.group("version").strip() if version_match else ""

    # Infer document type from the title (not from content semantics).
    title_lower = title.lower()
    if "runbook" in title_lower:
        doc_type = "runbook"
    elif "standard" in title_lower:
        doc_type = "standard"
    else:
        doc_type = "unknown"

    return {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "title": title,
        "status": status,
        "version": version,
        "doc_type": doc_type,
    }


def _safe_resolve(file_name: str) -> Path:
    """Resolve *file_name* under ``knowledge/`` and verify it stays inside.

    Raises
    ------
    ValueError
        If the resolved path escapes the ``knowledge/`` directory.
    """
    candidate = (KNOWLEDGE_DIR / file_name).resolve()
    knowledge_resolved = KNOWLEDGE_DIR.resolve()
    if not str(candidate).startswith(str(knowledge_resolved)):
        raise ValueError(
            f"Security: path '{file_name}' resolves outside the knowledge directory."
        )
    return candidate


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_knowledge_documents() -> list[dict[str, Any]]:
    """List all knowledge documents with their metadata.

    Returns
    -------
    list[dict]
        One dict per ``*.md`` file in ``knowledge/``, sorted by file name.
        Each dict contains: ``file_name``, ``file_path``, ``title``,
        ``status``, ``version``, ``doc_type``.

    Raises
    ------
    FileNotFoundError
        If the ``knowledge/`` directory does not exist.
    """
    if not KNOWLEDGE_DIR.exists():
        raise FileNotFoundError(f"Knowledge directory not found: {KNOWLEDGE_DIR}")

    documents: list[dict[str, Any]] = []

    for file_path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        content = file_path.read_text(encoding="utf-8-sig")
        meta = _extract_metadata(content, file_path)
        documents.append(meta)

    return documents


def get_knowledge_document(file_name: str) -> dict[str, Any]:
    """Retrieve a single knowledge document by file name.

    Parameters
    ----------
    file_name
        File name (e.g. ``01_application_performance_standard.md``).
        Only files inside ``knowledge/`` are accepted.

    Returns
    -------
    dict
        Keys: ``file_name``, ``file_path``, ``title``, ``status``,
        ``version``, ``doc_type``, ``content`` (raw Markdown).

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the path resolves outside ``knowledge/``.
    """
    file_path = _safe_resolve(file_name)

    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"Knowledge file not found: {file_path}")

    content = file_path.read_text(encoding="utf-8-sig")
    meta = _extract_metadata(content, file_path)
    meta["content"] = content
    return meta


def search_knowledge_documents(
    keyword: str | None = None,
    doc_type: str | None = None,
) -> list[dict[str, Any]]:
    """Search knowledge documents by keyword and/or document type.

    Parameters
    ----------
    keyword
        Case-insensitive keyword searched in the document **title** and
        **content**.  When ``None``, no keyword filter is applied.
    doc_type
        Filter by ``doc_type`` (``standard`` or ``runbook``),
        case-insensitive exact match.

    Returns
    -------
    list[dict]
        Matching documents (including ``content``), sorted by file name.

    Raises
    ------
    FileNotFoundError
        If the ``knowledge/`` directory does not exist.
    """
    if not KNOWLEDGE_DIR.exists():
        raise FileNotFoundError(f"Knowledge directory not found: {KNOWLEDGE_DIR}")

    results: list[dict[str, Any]] = []

    for file_path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        content = file_path.read_text(encoding="utf-8-sig")
        meta = _extract_metadata(content, file_path)

        if doc_type and meta["doc_type"].lower() != doc_type.lower():
            continue

        if keyword:
            haystack = (meta["title"] + " " + content).lower()
            if keyword.lower() not in haystack:
                continue

        meta["content"] = content
        results.append(meta)

    return results


if __name__ == "__main__":
    import json

    print("=== Knowledge document list ===")
    print(json.dumps(list_knowledge_documents(), indent=2))

    print("\n=== Retrieve one document ===")
    doc = get_knowledge_document("01_application_performance_standard.md")
    print(f"Title : {doc['title']}")
    print(f"Status: {doc['status']}")
    print(f"Type  : {doc['doc_type']}")
    print(f"Content preview:\n{doc['content'][:200]}")