@echo off
setlocal

cd /d "%~dp0"

if not defined PLAN_GOVERNOR_DB_URL (
    set "PLAN_GOVERNOR_DB_URL=sqlite:///./plan_governor.db"
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m server.main
) else (
    python -m server.main
)

endlocal
