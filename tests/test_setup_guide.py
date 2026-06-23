from __future__ import annotations

from server.services.setup_guide import build_setup_guide, render_cursor_connection_log


def test_build_setup_guide():
    guide = build_setup_guide()
    assert guide["ok"] is True
    assert "plan-governor" in guide["mcp_config"]["mcpServers"]
    assert guide["rule_template"].startswith("---")
    assert len(guide["available_tools"]) == 11
    assert "create_request" in guide["markdown"]
    assert guide["cursor_instructions"]


def test_build_setup_guide_custom_root(tmp_path):
    guide = build_setup_guide(project_root=str(tmp_path))
    assert guide["project_root"] == str(tmp_path.resolve())


def test_render_cursor_connection_log(tmp_path):
    lines = render_cursor_connection_log(tmp_path)
    text = "\n".join(lines)
    assert "Cursor connection guide" in text
    assert ".cursor/mcp.json" in text
    assert "plan-governor" in text
    assert "get_project_setup_guide" in text
