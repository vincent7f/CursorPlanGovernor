from __future__ import annotations

from server.services.setup_guide import build_setup_guide


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
