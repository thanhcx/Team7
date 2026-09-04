"""Agent Orchestration V0.1 for the I&O Operations Support Agent.

This package implements the orchestration layer that:
    1. Resolves the target system and time window from a user question.
    2. Retrieves system inventory and cross-domain evidence using existing
       read-only data tools.
    3. Retrieves approved standards and runbooks from the knowledge layer.
    4. Builds a grounded context and sends it to GreenNode MaaS.
    5. Returns a structured operational analysis response.

No existing tools, data, knowledge, or agent instructions are modified.
"""