# syntax=docker/dockerfile:1
# ----------------------------------------------------------------------------
# I&O Operations Support Agent — GreenNode AgentBase runtime image
#
# AgentBase runtime contract (HARD):
#   1. Listen on 0.0.0.0:8080  (platform routes all traffic here)
#   2. GET /health -> 200        (marks the runtime ACTIVE)
#
# The FastAPI app in api/main.py already exposes GET /health; we bind uvicorn
# to 0.0.0.0:8080 via the CMD below to satisfy contract #1.
# ----------------------------------------------------------------------------
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# --- Dependencies (cached layer) -------------------------------------------
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# --- Application code & runtime assets --------------------------------------
# agent/  -> config, greennode_client, orchestrator, agent_instruction.md
# api/    -> FastAPI entry point
# tools/  -> deterministic data tools (read-only, stdlib only)
# data/   -> synthetic CSV/log dataset (required by tools at runtime)
# knowledge/ -> runbooks & performance standards (required by knowledge_retrieval)
# web/    -> static frontend served by FastAPI (index.html, app.js, styles.css)
# NOTE: agent/skills/ is excluded via .dockerignore — it is dev tooling
#       (SKILL.md for AI coding agents), not runtime code.
COPY agent/ ./agent/
COPY api/   ./api/
COPY tools/ ./tools/
COPY data/  ./data/
COPY knowledge/ ./knowledge/
COPY web/   ./web/

# --- AgentBase runtime contract: port 8080 ----------------------------------
EXPOSE 8080

# Mirror the platform's health probe so `docker ps` / local runs surface a
# broken container the same way AgentBase would (status -> ERROR).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=4); sys.exit(0)" || exit 1

# Serve the FastAPI app on the contract port. --no-access-log keeps logs clean
# for the AgentBase log stream; remove it if you want request logs.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
