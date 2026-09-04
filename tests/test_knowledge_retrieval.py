"""Tests for ``tools/knowledge_retrieval.py``."""

from __future__ import annotations

import pytest

from tools.knowledge_retrieval import (
    get_knowledge_document,
    list_knowledge_documents,
    search_knowledge_documents,
)


# ---------------------------------------------------------------------------
# list_knowledge_documents
# ---------------------------------------------------------------------------

class TestListKnowledgeDocuments:
    def test_returns_four_documents(self):
        docs = list_knowledge_documents()
        assert len(docs) == 4

    def test_sorted_by_file_name(self):
        docs = list_knowledge_documents()
        names = [d["file_name"] for d in docs]
        assert names == sorted(names)

    def test_expected_file_names(self):
        docs = list_knowledge_documents()
        names = {d["file_name"] for d in docs}
        assert names == {
            "01_application_performance_standard.md",
            "02_storage_performance_standard.md",
            "03_application_slow_response_runbook.md",
            "04_storage_high_latency_runbook.md",
        }

    def test_metadata_keys(self):
        docs = list_knowledge_documents()
        expected_keys = {"file_name", "file_path", "title", "status", "version", "doc_type"}
        for doc in docs:
            assert set(doc.keys()) == expected_keys

    def test_all_approved_status(self):
        docs = list_knowledge_documents()
        for doc in docs:
            assert doc["status"] == "APPROVED-FOR-HACKATHON"

    def test_all_version_1(self):
        docs = list_knowledge_documents()
        for doc in docs:
            assert doc["version"] == "1.0"

    def test_doc_types(self):
        docs = list_knowledge_documents()
        by_name = {d["file_name"]: d["doc_type"] for d in docs}
        assert by_name["01_application_performance_standard.md"] == "standard"
        assert by_name["02_storage_performance_standard.md"] == "standard"
        assert by_name["03_application_slow_response_runbook.md"] == "runbook"
        assert by_name["04_storage_high_latency_runbook.md"] == "runbook"


# ---------------------------------------------------------------------------
# get_knowledge_document
# ---------------------------------------------------------------------------

class TestGetKnowledgeDocument:
    def test_retrieve_application_standard(self):
        doc = get_knowledge_document("01_application_performance_standard.md")
        assert doc["title"] == "Application Performance Standard — Synthetic Hackathon"
        assert doc["doc_type"] == "standard"
        assert "content" in doc
        assert "Response Time" in doc["content"]

    def test_retrieve_storage_standard(self):
        doc = get_knowledge_document("02_storage_performance_standard.md")
        assert doc["title"] == "Storage Performance Standard — Synthetic Hackathon"
        assert doc["doc_type"] == "standard"
        assert "Storage Latency" in doc["content"]

    def test_retrieve_app_runbook(self):
        doc = get_knowledge_document("03_application_slow_response_runbook.md")
        assert "Runbook" in doc["title"]
        assert doc["doc_type"] == "runbook"
        assert "Diagnostic Steps" in doc["content"]

    def test_retrieve_storage_runbook(self):
        doc = get_knowledge_document("04_storage_high_latency_runbook.md")
        assert "Runbook" in doc["title"]
        assert doc["doc_type"] == "runbook"
        assert "RCA Hypothesis" in doc["content"]

    def test_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            get_knowledge_document("nonexistent.md")

    def test_path_traversal_raises(self):
        with pytest.raises(ValueError):
            get_knowledge_document("../README.md")

    def test_content_is_raw_markdown(self):
        doc = get_knowledge_document("01_application_performance_standard.md")
        assert doc["content"].startswith("# Application Performance Standard")


# ---------------------------------------------------------------------------
# search_knowledge_documents
# ---------------------------------------------------------------------------

class TestSearchKnowledgeDocuments:
    def test_no_filters_returns_all(self):
        docs = search_knowledge_documents()
        assert len(docs) == 4

    def test_filter_by_doc_type_standard(self):
        docs = search_knowledge_documents(doc_type="standard")
        assert len(docs) == 2
        assert all(d["doc_type"] == "standard" for d in docs)

    def test_filter_by_doc_type_runbook(self):
        docs = search_knowledge_documents(doc_type="runbook")
        assert len(docs) == 2
        assert all(d["doc_type"] == "runbook" for d in docs)

    def test_search_keyword_storage(self):
        docs = search_knowledge_documents(keyword="storage")
        # Storage standard + storage runbook + app runbook mentions storage
        assert len(docs) >= 2

    def test_search_keyword_response_time(self):
        docs = search_knowledge_documents(keyword="response time")
        assert len(docs) >= 2

    def test_search_keyword_in_runbooks(self):
        docs = search_knowledge_documents(keyword="Diagnostic", doc_type="runbook")
        assert len(docs) == 2

    def test_search_no_match(self):
        docs = search_knowledge_documents(keyword="nonexistent_topic_xyz123")
        assert docs == []

    def test_results_include_content(self):
        docs = search_knowledge_documents(doc_type="standard")
        for doc in docs:
            assert "content" in doc

    def test_doc_type_case_insensitive(self):
        docs_lower = search_knowledge_documents(doc_type="standard")
        docs_upper = search_knowledge_documents(doc_type="STANDARD")
        assert len(docs_lower) == len(docs_upper)