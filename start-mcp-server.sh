#!/usr/bin/env bash

cd "$(dirname "$0")"

if [ -z "${PLAN_GOVERNOR_DB_URL:-}" ]; then
    export PLAN_GOVERNOR_DB_URL="sqlite:///./plan_governor.db"
fi

if [ -z "${PLAN_GOVERNOR_MCP_TRANSPORT:-}" ]; then
    export PLAN_GOVERNOR_MCP_TRANSPORT=streamable-http
fi

if [ -z "${PLAN_GOVERNOR_MCP_HOST:-}" ]; then
    export PLAN_GOVERNOR_MCP_HOST=0.0.0.0
fi

if [ -z "${PLAN_GOVERNOR_MCP_PORT:-}" ]; then
    export PLAN_GOVERNOR_MCP_PORT=8000
fi

if [ -f ".venv/bin/python" ]; then
    ".venv/bin/python" -m server.main
else
    python -m server.main
fi
