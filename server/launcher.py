"""Cross-platform helpers to launch the MCP server for Cursor stdio transport."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_URL = "sqlite:///./plan_governor.db"
LAUNCHER_SCRIPT = "launch_mcp_stdio.py"
WORKSPACE_FOLDER = "${workspaceFolder}"


def resolve_project_root(root: Path | None = None) -> Path:
    return (root or PROJECT_ROOT).resolve()


def resolve_venv_python(root: Path | None = None) -> Path | None:
    project_root = resolve_project_root(root)
    if sys.platform == "win32":
        candidate = project_root / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = project_root / ".venv" / "bin" / "python"
    return candidate if candidate.is_file() else None


def cursor_python_command() -> str:
    return "python"


def cursor_python_args(root: Path | None = None, portable: bool = True) -> list[str]:
    project_root = resolve_project_root(root)
    launcher = f"{WORKSPACE_FOLDER}/{LAUNCHER_SCRIPT}" if portable else str(project_root / LAUNCHER_SCRIPT)
    return [launcher]


def stdio_env() -> dict[str, str]:
    return {
        "PLAN_GOVERNOR_DB_URL": DEFAULT_DB_URL,
        "PLAN_GOVERNOR_MCP_TRANSPORT": "stdio",
    }


def build_stdio_mcp_entry(root: Path | None = None, portable: bool = True) -> dict:
    project_root = resolve_project_root(root)
    return {
        "command": cursor_python_command(),
        "args": cursor_python_args(project_root, portable=portable),
        "cwd": WORKSPACE_FOLDER if portable else str(project_root),
        "env": stdio_env(),
    }


def launch_stdio(root: Path | None = None) -> None:
    """Launch MCP server in stdio mode, preferring the project virtualenv."""
    project_root = resolve_project_root(root)
    os.chdir(project_root)

    for key, value in stdio_env().items():
        os.environ.setdefault(key, value)

    venv_python = resolve_venv_python(project_root)
    if venv_python is not None:
        os.execv(str(venv_python), [str(venv_python), "-m", "server.main"])

    from server.main import main

    main()
