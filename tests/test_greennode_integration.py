"""Integration test for IOOperationsOrchestrator.generate_response().

This test makes a **real** GreenNode MaaS call. It does not mock
``AgentConfig``, ``GreenNodeClient``, or ``client.chat()``.
It relies on the existing GreenNode configuration mechanism (environment
variables such as ``GREENNODE_API_KEY``).

Run only when the GreenNode environment is properly configured.
"""

import re

from agent.orchestrator import IOOperationsOrchestrator


def test_generate_response_real_greennode_call():
    """Verify generate_response() returns a valid response from GreenNode MaaS.

    Uses a generic in-memory grounded context with synthetic test data.
    Does not assert any specific RCA, health result, or expected answer.
    """
    grounded_context = {
        "request": "Analyze the health of Test Service for the provided time window.",
        "system": {
            "system_id": "SYS-TEST-001",
            "system_name": "Test Service",
        },
        "time_window": {
            "start": "2026-09-10T10:00:00",
            "end": "2026-09-10T10:15:00",
        },
        "inventory": {
            "application": "test-app-01",
            "vm": "test-vm-01",
        },
        "operational_evidence": {
            "application": [
                {
                    "timestamp": "2026-09-10T10:05:00",
                    "response_time_ms": 240,
                    "error_rate_pct": 0.4,
                }
            ],
            "server": [
                {
                    "timestamp": "2026-09-10T10:05:00",
                    "cpu_pct": 35,
                    "memory_pct": 48,
                }
            ],
            "vmware": [],
            "storage": [],
            "network": [],
            "alerts": [],
            "logs": [],
        },
        "knowledge": [],
    }

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.generate_response(grounded_context)

    # Integration-level assertions only.
    assert isinstance(result, dict)
    assert result["status"] == "ok", result.get("message", "Unknown GreenNode error")
    assert result["response"] is not None
    assert isinstance(result["response"], str)
    assert len(result["response"]) > 0


def test_agent_instruction_output_contract():
    """Verify generate_response() follows the Agent Instruction output contract.

    Uses a small generic synthetic grounded context with neutral evidence.
    Does not use any project use-case data, CSV, logs, or knowledge files.
    Does not mock GreenNodeClient — this is a real GreenNode MaaS call.
    Checks the 11-section output contract only, not reasoning correctness.
    """
    grounded_context = {
        "request": (
            "Analyze the health of TEST-SERVICE for the time window "
            "2026-08-30 09:00 to 09:10."
        ),
        "system": {
            "name": "TEST-SERVICE",
            "type": "Generic Application Service",
        },
        "time_window": {
            "start": "2026-08-30T09:00:00",
            "end": "2026-08-30T09:10:00",
        },
        "operational_evidence": {
            "application": [
                {
                    "timestamp": "2026-08-30T09:00:00",
                    "response_time_ms": 200,
                    "error_rate_pct": 0.2,
                },
                {
                    "timestamp": "2026-08-30T09:10:00",
                    "response_time_ms": 650,
                    "error_rate_pct": 1.5,
                },
            ],
            "server": [
                {
                    "timestamp": "2026-08-30T09:00:00",
                    "cpu_pct": 40,
                    "memory_pct": 55,
                },
                {
                    "timestamp": "2026-08-30T09:10:00",
                    "cpu_pct": 40,
                    "memory_pct": 55,
                },
            ],
            "network": [
                {
                    "timestamp": "2026-08-30T09:00:00",
                    "note": "network latency remained stable",
                },
            ],
            "storage": [
                {
                    "timestamp": "2026-08-30T09:00:00",
                    "note": "storage latency remained stable",
                },
            ],
            "vmware": [],
            "alerts": [],
            "logs": [],
        },
        "knowledge": [
            {
                "doc_type": "standard",
                "title": "Generic Operational Analysis Standard",
                "content": (
                    "Analysis must correlate evidence across relevant "
                    "domains before assigning a cause."
                ),
            },
            {
                "doc_type": "runbook",
                "title": "Generic Insufficient Evidence Runbook",
                "content": (
                    "Insufficient evidence must be explicitly identified "
                    "in the analysis output."
                ),
            },
        ],
    }

    orchestrator = IOOperationsOrchestrator()
    result = orchestrator.generate_response(grounded_context)

    # --- Status assertion (existing diagnostic pattern) ---
    assert result["status"] == "ok", result.get("message", "Unknown GreenNode error")

    # --- Response extraction ---
    response = result["response"]
    assert isinstance(response, str)
    assert len(response) > 0

    response_lower = response.lower()

    # --- Verify all 11 required output sections (case-insensitive substring) ---
    required_sections = [
        "Overall Health",
        "Scope",
        "Affected Components",
        "Findings",
        "Evidence",
        "RCA Hypothesis",
        "Standard / Baseline Assessment",
        "Recommendation",
        "Knowledge References",
        "Confidence",
        "Insufficient Evidence",
    ]
    for section in required_sections:
        assert section.lower() in response_lower, (
            f"Missing required output section: {section!r}"
        )

    # --- Verify no confirmed root cause is claimed (case-insensitive) ---
    # Reject only explicit positive confirmed-root-cause headings and
    # declarations.  Negated/uncertainty language such as "no confirmed root
    # cause", "root cause cannot be confirmed", or "insufficient evidence to
    # confirm root cause" remains allowed.
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

    # --- Verify no remediation was executed (case-insensitive) ---
    forbidden_remediation_phrases = [
        "remediation executed",
        "change executed",
        "configuration changed",
        "automatically remediated",
    ]
    for phrase in forbidden_remediation_phrases:
        assert phrase.lower() not in response_lower, (
            f"Response indicates remediation was executed: {phrase!r}"
        )
