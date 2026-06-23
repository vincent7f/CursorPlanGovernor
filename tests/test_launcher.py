from __future__ import annotations

import sys
from pathlib import Path

from server.launcher import build_stdio_mcp_entry, cursor_python_command, resolve_venv_python


def test_resolve_venv_python(tmp_path):
    if sys.platform == "win32":
        venv_dir = tmp_path / ".venv" / "Scripts"
        python_name = "python.exe"
    else:
        venv_dir = tmp_path / ".venv" / "bin"
        python_name = "python"
    venv_dir.mkdir(parents=True)
    python = venv_dir / python_name
    python.write_text("", encoding="utf-8")

    assert resolve_venv_python(tmp_path) == python.resolve()


def test_build_stdio_mcp_entry_portable():
    entry = build_stdio_mcp_entry(portable=True)
    assert entry["command"] == cursor_python_command()
    assert entry["args"] == ["${workspaceFolder}/launch_mcp_stdio.py"]
    assert entry["cwd"] == "${workspaceFolder}"
    assert entry["env"]["PLAN_GOVERNOR_MCP_TRANSPORT"] == "stdio"


def test_build_stdio_mcp_entry_resolved(tmp_path):
    entry = build_stdio_mcp_entry(tmp_path, portable=False)
    assert entry["cwd"] == str(tmp_path.resolve())
    assert entry["args"] == [str((tmp_path / "launch_mcp_stdio.py").resolve())]
