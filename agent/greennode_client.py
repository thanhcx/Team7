"""GreenNode MaaS client for Agent Orchestration V0.1.

Wraps the OpenAI-compatible GreenNode MaaS endpoint using the ``openai``
Python SDK.  The client is intentionally thin: it handles configuration,
request construction, and response extraction so that the orchestrator
can focus on evidence gathering and context building.

Design notes
------------
- The client accepts an :class:`~agent.config.AgentConfig` so that tests
  can inject a dummy config without touching environment variables.
- A ``mock_response`` parameter on :meth:`GreenNodeClient.chat` allows
  tests to bypass the real HTTP call entirely.
- No retry / backoff logic is included in V0.1; callers receive the
  raw exception from the SDK on failure.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openai import OpenAI

from .config import AgentConfig


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
# The agent instruction markdown file is the single runtime source of truth
# for the GreenNode system prompt.  The path is resolved relative to this
# module so that loading does not depend on the current working directory.

_INSTRUCTION_FILE = Path(__file__).resolve().parent / "agent_instruction.md"

try:
    SYSTEM_PROMPT = _INSTRUCTION_FILE.read_text(encoding="utf-8").strip()
except FileNotFoundError as exc:
    raise RuntimeError(
        f"Agent instruction file not found: {_INSTRUCTION_FILE}"
    ) from exc
except OSError as exc:
    raise RuntimeError(
        f"Unable to read agent instruction file {_INSTRUCTION_FILE}: {exc}"
    ) from exc

if not SYSTEM_PROMPT:
    raise RuntimeError(
        f"Agent instruction file is empty: {_INSTRUCTION_FILE}"
    )


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class GreenNodeClient:
    """Thin wrapper around the GreenNode MaaS OpenAI-compatible endpoint.

    Parameters
    ----------
    config
        The :class:`AgentConfig` with credentials and model settings.
    """

    def __init__(self, config: AgentConfig) -> None:
        self._config = config
        self._client: OpenAI | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self) -> OpenAI:
        """Lazily construct the underlying ``OpenAI`` client.

        Raises
        ------
        ValueError
            If no API key is configured.
        """
        if self._client is not None:
            return self._client

        if not self._config.has_api_key():
            raise ValueError(
                "GREENNODE_API_KEY is not set. "
                "Configure the environment variable or pass a mock client."
            )

        self._client = OpenAI(
            base_url=self._config.base_url,
            api_key=self._config.api_key,
        )
        return self._client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(
        self,
        user_message: str,
        *,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        mock_response: str | None = None,
    ) -> str:
        """Send a single-turn chat completion request to GreenNode MaaS.

        Parameters
        ----------
        user_message
            The grounded context / user question to send to the model.
        system_prompt
            Override for the default system prompt.  When ``None`` the
            built-in I&O Operations Support Agent prompt is used.
        temperature
            Override for the configured temperature.
        max_tokens
            Override for the configured max tokens.
        mock_response
            When provided, the method returns this string immediately
            **without** calling the real API.  Intended for tests and
            dry-run mode.

        Returns
        -------
        str
            The text content of the model's response.

        Raises
        ------
        ValueError
            If no API key is configured and ``mock_response`` is not
            provided.
        """
        if mock_response is not None:
            return mock_response

        client = self._get_client()

        response = client.chat.completions.create(
            model=self._config.model,
            messages=[
                {"role": "system", "content": system_prompt or SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature if temperature is not None else self._config.temperature,
            max_tokens=max_tokens if max_tokens is not None else self._config.max_tokens,
        )

        return self._extract_content(response)

    @staticmethod
    def _extract_content(response: Any) -> str:
        """Extract the text content from an OpenAI chat completion response."""
        # Standard OpenAI response structure.
        try:
            return response.choices[0].message.content
        except (AttributeError, IndexError, KeyError, TypeError):
            pass

        # Fallback for dict-like responses (e.g. raw JSON).
        if isinstance(response, dict):
            try:
                return response["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                pass

        return str(response)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @property
    def config(self) -> AgentConfig:
        """Return the configuration used by this client."""
        return self._config