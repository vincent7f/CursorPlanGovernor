#!/usr/bin/env bash

cd "$(dirname "$0")"

if [ -z "${PLAN_GOVERNOR_DB_URL:-}" ]; then
    export PLAN_GOVERNOR_DB_URL="sqlite:///./plan_governor.db"
fi

if [ -f ".venv/bin/python" ]; then
    ".venv/bin/python" -m server.main
else
    python -m server.main
fi
