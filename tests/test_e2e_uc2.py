"""End-to-end test for UC2: Storage Degradation scenario.

This test makes a **real** GreenNode MaaS call through the full
IOOperationsOrchestrator pipeline. It does not mock any component.
It uses the actual synthetic project data and knowledge sources.

Run only when the GreenNode environment is properly configured.
"""

import re

from agent.orchestrator import IOOperationsOrchestrator


def test_uc2_storage_degradation_end_to_end():
    """Validate the complete I&O Operations Support Agent pipeline for UC2.

    Scenario: Internet Banking application slowdown starting ~10:00 on
    2026-08-26. The synthetic data shows application response time
    degrading while DB connection pool and thread pool remain normal.
    Server, VMware, and Network metrics remain stable. Storage latency
    increases significantly during the same time window with a
    corresponding storage workload increase.

    This is a real GreenNode integration test — no mocks.
    """
    user_question = (
        "Internet Banking đang chậm từ khoảng 10:00 ngày 2026-08-26. "
        "Kiểm tra giúp tôi nguyên nhân có thể nằm ở đâu?"
    )

    result = IOOperationsOrchestrator().run(user_question)

    # --- 1. Orchestration completes successfully ---
    assert result["status"] == "ok", (
        f"Orchestration did not complete successfully. "
        f"Status: {result.get('status')}, "
        f"Message: {result.get('message', 'N/A')}"
    )

    # --- 2. Non-empty final GreenNode response ---
    response = result["response"]
    assert isinstance(response, str), (
        f"Response is not a string. Got: {type(response).__name__}"
    )
    assert len(response) > 0, "Response is empty."

    response_lower = response.lower()

    # --- 3. Application response time degradation is detected ---
    app_response_keywords = [
        "response time",
        "response_time",
        "response_time_ms",
        "slow response",
        "application slow",
        "application slowness",
        "application degradation",
        "application performance",
        "increased response",
        "high response",
        "degraded response",
    ]
    assert any(kw in response_lower for kw in app_response_keywords), (
        "Response does not detect application response time degradation. "
        "Expected at least one of: " + ", ".join(app_response_keywords)
    )

    # --- 4. Storage latency degradation is detected ---
    storage_latency_keywords = [
        "storage latency",
        "latency",
        "storage degradation",
        "storage performance",
        "high latency",
        "increased latency",
        "latency spike",
        "storage slow",
        "storage slowness",
        "iops",
        "queue depth",
        "storage latency spike",
        "storage latency increase",
    ]
    assert any(kw in response_lower for kw in storage_latency_keywords), (
        "Response does not detect storage latency degradation. "
        "Expected at least one of: " + ", ".join(storage_latency_keywords)
    )

    # --- 5. DB connection pool is recognized as NOT saturated ---
    db_pool_keywords = [
        "db connection pool",
        "database connection pool",
        "connection pool",
        "db pool",
        "db_connection_pool",
        "connection pool utilization",
        "pool utilization",
    ]
    assert any(kw in response_lower for kw in db_pool_keywords), (
        "Response does not reference DB connection pool at all. "
        "Expected at least one of: " + ", ".join(db_pool_keywords)
    )
    # The response should indicate the pool is normal/healthy/not saturated
    db_pool_normal_state_keywords = [
        "pool normal",
        "pool healthy",
        "pool not saturated",
        "pool not exhausted",
        "pool not critical",
        "pool within",
        "pool stable",
        "pool is normal",
        "pool is healthy",
        "pool remains normal",
        "pool remains healthy",
        "pool remains stable",
        "connection pool normal",
        "connection pool healthy",
        "connection pool not saturated",
        "connection pool stable",
        "connection pool remains",
        "db pool normal",
        "db pool healthy",
        "db pool not saturated",
        "db pool stable",
        "not saturated",
        "not exhausted",
        "within threshold",
        "within limit",
        "below threshold",
        "normal range",
        "healthy range",
    ]
    assert any(kw in response_lower for kw in db_pool_normal_state_keywords), (
        "Response does not indicate DB connection pool is normal/healthy. "
        "Expected at least one of: " + ", ".join(db_pool_normal_state_keywords)
    )

    # --- 6. Server is NOT identified as the primary anomaly ---
    _assert_not_primary_cause(response, "server", "Server")
    _assert_not_primary_cause(response, "cpu", "CPU")
    _assert_not_primary_cause(response, "memory", "Memory")

    # --- 7. VMware is NOT identified as the primary anomaly ---
    _assert_not_primary_cause(response, "vmware", "VMware")
    _assert_not_primary_cause(response, "virtualization", "Virtualization")
    _assert_not_primary_cause(response, "cpu ready", "CPU Ready")
    _assert_not_primary_cause(response, "balloon", "Ballooning")

    # --- 8. Network is NOT identified as the primary anomaly ---
    _assert_not_primary_cause(response, "network", "Network")
    _assert_not_primary_cause(response, "packet loss", "Packet Loss")
    _assert_not_primary_cause(response, "interface error", "Interface Error")

    # --- 9. RCA Hypothesis points to Storage performance degradation ---
    storage_rca_keywords = [
        "storage degradation",
        "storage performance degradation",
        "storage latency",
        "storage issue",
        "storage problem",
        "storage bottleneck",
        "storage contention",
        "storage high latency",
        "storage latency spike",
        "storage latency increase",
        "storage is the",
        "storage as the",
        "storage-related",
        "storage related",
        "i/o contention",
        "io contention",
        "disk latency",
        "datastore latency",
        "storage subsystem",
    ]
    assert any(kw in response_lower for kw in storage_rca_keywords), (
        "Response does not point to Storage performance degradation "
        "as the RCA Hypothesis. "
        "Expected at least one of: " + ", ".join(storage_rca_keywords)
    )

    # --- 10. DB connection pool exhaustion is NOT the primary RCA ---
    _assert_not_primary_cause(response, "db connection pool", "DB connection pool")
    _assert_not_primary_cause(response, "database connection pool", "Database connection pool")
    _assert_not_primary_cause(response, "connection pool", "Connection pool")
    _assert_not_primary_cause(response, "pool exhaustion", "Pool exhaustion")
    _assert_not_primary_cause(response, "pool saturation", "Pool saturation")

    # --- 11. Response distinguishes RCA Hypothesis from confirmed root cause ---
    assert "rca hypothesis" in response_lower or "hypothesis" in response_lower, (
        "Response does not contain RCA Hypothesis — "
        "it must distinguish hypothesis from confirmed root cause."
    )
    _assert_no_confirmed_root_cause(response)

    # --- 12. Response contains Evidence ---
    assert "evidence" in response_lower, (
        "Response does not contain an Evidence section."
    )

    # --- 13. Response contains Standard / Baseline Assessment ---
    standard_keywords = [
        "standard",
        "baseline",
        "threshold",
        "standard/baseline",
        "baseline assessment",
        "standard assessment",
    ]
    assert any(kw in response_lower for kw in standard_keywords), (
        "Response does not contain a Standard / Baseline Assessment section. "
        "Expected at least one of: " + ", ".join(standard_keywords)
    )

    # --- 14. Response contains Recommendation / Next Actions ---
    recommendation_keywords = [
        "recommendation",
        "recommend",
        "next action",
        "next step",
        "suggested action",
        "remediation",
        "mitigation",
    ]
    assert any(kw in response_lower for kw in recommendation_keywords), (
        "Response does not contain a Recommendation / Next Actions section. "
        "Expected at least one of: " + ", ".join(recommendation_keywords)
    )

    # --- 15. Response contains Confidence ---
    assert "confidence" in response_lower, (
        "Response does not contain a Confidence section."
    )

    # --- 16. Response must NOT indicate remediation was executed ---
    remediation_executed_phrases = [
        "remediation executed",
        "change executed",
        "configuration changed",
        "automatically remediated",
        "remediation applied",
        "fix applied",
        "action taken",
        "changes applied",
    ]
    for phrase in remediation_executed_phrases:
        assert phrase not in response_lower, (
            f"Response indicates remediation was executed: {phrase!r}"
        )


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _assert_not_primary_cause(response: str, domain: str, label: str):
    """Assert that the response does not claim *domain* as the primary cause.

    Checks line-by-line for explicit positive causal attribution. Mentions
    of the domain as normal/stable/no-degradation are allowed.
    """
    causal_indicators = [
        "primary cause",
        "root cause",
        "main cause",
        "likely cause",
        "primary reason",
        "root reason",
        "main reason",
        "caused by",
        "primary issue",
        "main issue",
        "likely issue",
        "primary factor",
        "main factor",
    ]
    negation_words = (
        "not", "no ", "isn't", "wasn't", "doesn't", "didn't",
        "rather than", "instead of", "unlikely", "cannot",
        "can't", "without",
    )

    for line in response.splitlines():
        line_lower = line.lower()
        if domain in line_lower:
            for indicator in causal_indicators:
                if indicator in line_lower:
                    if not any(neg in line_lower for neg in negation_words):
                        raise AssertionError(
                            f"Response claims {label} degradation as the "
                            f"primary cause. Line: {line.strip()!r}"
                        )


def _assert_no_confirmed_root_cause(response: str):
    """Assert that the response does not claim a confirmed root cause.

    Rejects explicit positive confirmed-root-cause headings and declarations.
    Negated/uncertainty language remains allowed.
    """
    _negation_words = (
        "no ", "not ", "cannot ", "can't ", "without ",
        "insufficient ", "unable ", "unconfirmed ",
    )

    for line in response.splitlines():
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        # Reject confirmed/definitive root-cause headings:
        #   "# Root Cause", "## Root Cause",
        #   "# Confirmed Root Cause", "## Confirmed Root Cause",
        #   "# Definitive Root Cause", "## Definitive Root Cause"
        if re.match(
            r'#{1,2}\s+(?:Confirmed\s+|Definitive\s+)?Root\s+Cause\b',
            line_stripped,
            re.IGNORECASE,
        ):
            raise AssertionError(
                f"Response claims a confirmed root cause via heading: "
                f"{line_stripped!r}"
            )

        # Reject explicit positive declarations such as:
        #   "Confirmed Root Cause:" / "Definitive Root Cause:"
        # unless preceded by negation/uncertainty language on the same line.
        decl_match = re.search(
            r'(?:Confirmed\s+Root\s+Cause|Definitive\s+Root\s+Cause)\s*:',
            line_stripped,
            re.IGNORECASE,
        )
        if decl_match:
            preceding = line_lower[:decl_match.start()]
            is_negated = any(neg in preceding for neg in _negation_words)
            assert is_negated, (
                f"Response claims a confirmed root cause via declaration: "
                f"{line_stripped!r}"
            )