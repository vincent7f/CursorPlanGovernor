@echo off
setlocal

cd /d "%~dp0"

if not defined PLAN_GOVERNOR_DB_URL (
    set "PLAN_GOVERNOR_DB_URL=sqlite:///./plan_governor.db"
)

if not defined PLAN_GOVERNOR_MCP_TRANSPORT (
    set "PLAN_GOVERNOR_MCP_TRANSPORT=streamable-http"
)

if not defined PLAN_GOVERNOR_MCP_HOST (
    set "PLAN_GOVERNOR_MCP_HOST=0.0.0.0"
)

if not defined PLAN_GOVERNOR_MCP_PORT (
    set "PLAN_GOVERNOR_MCP_PORT=8000"
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m server.main
) else (
    python -m server.main
)

endlocal
