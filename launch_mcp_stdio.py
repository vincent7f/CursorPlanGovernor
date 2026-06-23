#!/usr/bin/env python3
"""Cursor MCP stdio launcher (stdlib only). Re-execs with project .venv when present."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _venv_python() -> Path | None:
    if sys.platform == "win32":
        candidate = ROOT / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = ROOT / ".venv" / "bin" / "python"
    return candidate if candidate.is_file() else None


def main() -> None:
    os.chdir(ROOT)
    os.environ.setdefault("PLAN_GOVERNOR_DB_URL", "sqlite:///./plan_governor.db")
    os.environ.setdefault("PLAN_GOVERNOR_MCP_TRANSPORT", "stdio")

    venv_python = _venv_python()
    if venv_python is not None:
        os.execv(str(venv_python), [str(venv_python), "-m", "server.main"])

    runpy.run_module("server.main", run_name="__main__")


if __name__ == "__main__":
    main()
