"""End-to-end test for UC1: Application Degradation scenario.

This test makes a **real** GreenNode MaaS call through the full
IOOperationsOrchestrator pipeline. It does not mock any component.
It uses the actual synthetic project data and knowledge sources.

Run only when the GreenNode environment is properly configured.
"""

import re

from agent.orchestrator import IOOperationsOrchestrator


def test_uc1_application_degradation_end_to_end():
    """Validate the complete I&O Operations Support Agent pipeline for UC1.

    Scenario: Internet Banking application degradation starting ~14:00 on
    2026-08-25. The synthetic data shows application response time and error
    rate spiking with DB connection pool saturation, while server, VMware,
    storage, and network metrics remain stable.

    This is a real GreenNode integration test — no mocks.
    """
    user_question = (
        "Internet Banking đang chậm từ khoảng 14:00 ngày 2026-08-25. "
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

    # --- 3. Response identifies application-layer degradation ---
    app_degradation_keywords = [
        "application degradation",
        "application slow",
        "application slowness",
        "application performance",
        "response time",
        "application layer",
        "application-level",
        "app degradation",
    ]
    assert any(kw in response_lower for kw in app_degradation_keywords), (
        "Response does not identify application-layer degradation. "
        "Expected at least one of: " + ", ".join(app_degradation_keywords)
    )

    # --- 4. Evidence includes/references application response-time degradation ---
    response_time_keywords = [
        "response time",
        "response_time",
        "response_time_ms",
        "slow response",
        "1200",
        "780",
        "950",
        "high latency",
        "increased latency",
    ]
    assert any(kw in response_lower for kw in response_time_keywords), (
        "Response does not reference application response-time degradation. "
        "Expected at least one of: " + ", ".join(response_time_keywords)
    )

    # --- 5. Evidence includes/references application error increase ---
    error_rate_keywords = [
        "error rate",
        "error_rate",
        "error_rate_pct",
        "error increase",
        "error spike",
        "8.0",
        "4.5",
        "high error",
        "increased error",
    ]
    assert any(kw in response_lower for kw in error_rate_keywords), (
        "Response does not reference application error rate increase. "
        "Expected at least one of: " + ", ".join(error_rate_keywords)
    )

    # --- 6. Response identifies DB connection pool pressure/exhaustion/saturation
    #        as the primary RCA Hypothesis ---
    db_pool_keywords = [
        "db connection pool",
        "database connection pool",
        "connection pool",
        "db pool",
        "pool exhaustion",
        "pool saturation",
        "pool pressure",
        "unable to acquire",
        "connection pool utilization",
        "db_connection_pool",
        "acquire database connection",
        "acquire db connection",
    ]
    assert any(kw in response_lower for kw in db_pool_keywords), (
        "Response does not identify database connection pool "
        "pressure/exhaustion/saturation as the RCA Hypothesis. "
        "Expected at least one of: " + ", ".join(db_pool_keywords)
    )

    # --- 7. Response must NOT claim storage degradation as primary cause ---
    _assert_not_primary_cause(response, "storage", "Storage")

    # --- 8. Response must NOT claim network degradation as primary cause ---
    _assert_not_primary_cause(response, "network", "Network")

    # --- 9. Response must NOT claim VMware degradation as primary cause ---
    _assert_not_primary_cause(response, "vmware", "VMware")
    _assert_not_primary_cause(response, "virtualization", "Virtualization")

    # --- 10. Response distinguishes RCA Hypothesis from confirmed root cause ---
    assert "rca hypothesis" in response_lower or "hypothesis" in response_lower, (
        "Response does not contain RCA Hypothesis — "
        "it must distinguish hypothesis from confirmed root cause."
    )
    _assert_no_confirmed_root_cause(response)

    # --- 11. Response contains Evidence ---
    assert "evidence" in response_lower, (
        "Response does not contain an Evidence section."
    )

    # --- 12. Response contains Recommendation ---
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
        "Response does not contain a Recommendation section. "
        "Expected at least one of: " + ", ".join(recommendation_keywords)
    )

    # --- 13. Response contains Confidence ---
    assert "confidence" in response_lower, (
        "Response does not contain a Confidence section."
    )

    # --- 14. Response must NOT indicate remediation was executed ---
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