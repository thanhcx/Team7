"""Configuration for Agent Orchestration V0.1.

All runtime settings are read from environment variables so that no
secrets or deployment-specific values are hard-coded.

Environment variables
---------------------
``GREENNODE_API_KEY``
    API key for the GreenNode MaaS endpoint.  **Required** when making
    real LLM calls; may be unset in tests that inject a mock client.

``GREENNODE_BASE_URL``
    Base URL of the GreenNode MaaS OpenAI-compatible endpoint.
    Defaults to the known hackathon endpoint.

``GREENNODE_MODEL``
    Model identifier to use on the GreenNode MaaS endpoint.
    Defaults to the known hackathon model.

``AGENT_LLM_TEMPERATURE``
    Sampling temperature for the LLM (default ``0.2``).

``AGENT_LLM_MAX_TOKENS``
    Maximum tokens for the LLM response (default ``4096``).

``AGENT_LOG_LEVEL``
    Logging level for the agent package (default ``INFO``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1"
DEFAULT_MODEL = "z-ai/glm-5.2-hackathon"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 4096
DEFAULT_LOG_LEVEL = "INFO"


def _get_env(name: str, default: str | None = None) -> str | None:
    """Return the value of *name* from the environment or *default*."""
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _get_float_env(name: str, default: float) -> float:
    """Return a float from the environment or *default* on parse failure."""
    raw = _get_env(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except (ValueError, TypeError):
        return default


def _get_int_env(name: str, default: int) -> int:
    """Return an int from the environment or *default* on parse failure."""
    raw = _get_env(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AgentConfig:
    """Immutable configuration for the orchestration agent.

    Instances are created via :func:`load_config` which reads environment
    variables.  Tests may construct ``AgentConfig`` directly to inject
    test-specific values.
    """

    api_key: str | None
    base_url: str
    model: str
    temperature: float
    max_tokens: int
    log_level: str

    def has_api_key(self) -> bool:
        """Return ``True`` when a non-empty API key is configured."""
        return bool(self.api_key)


def load_config() -> AgentConfig:
    """Load configuration from environment variables.

    Returns
    -------
    AgentConfig
        A frozen configuration object.

    Notes
    -----
    ``api_key`` may be ``None`` when ``GREENNODE_API_KEY`` is not set.
    The orchestrator and CLI use this to decide whether to call the
    real LLM or return a dry-run / evidence-only response.
    """
    return AgentConfig(
        api_key=_get_env("GREENNODE_API_KEY"),
        base_url=_get_env("GREENNODE_BASE_URL", DEFAULT_BASE_URL) or DEFAULT_BASE_URL,
        model=_get_env("GREENNODE_MODEL", DEFAULT_MODEL) or DEFAULT_MODEL,
        temperature=_get_float_env("AGENT_LLM_TEMPERATURE", DEFAULT_TEMPERATURE),
        max_tokens=_get_int_env("AGENT_LLM_MAX_TOKENS", DEFAULT_MAX_TOKENS),
        log_level=_get_env("AGENT_LOG_LEVEL", DEFAULT_LOG_LEVEL) or DEFAULT_LOG_LEVEL,
    )