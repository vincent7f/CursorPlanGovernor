from __future__ import annotations

import json
import sys
from pathlib import Path

from server.config import build_mcp_http_url, get_lan_ip, get_mcp_http_path, get_mcp_port
from server.launcher import build_stdio_mcp_entry

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

ALL_TOOLS = [
    {
        "name": "create_request",
        "phase": "planning",
        "description": "创建新需求入口，作为计划治理的起点。",
    },
    {
        "name": "plan_feature",
        "phase": "planning",
        "description": "生成首版计划 revision 并持久化任务树。",
    },
    {
        "name": "replan_feature",
        "phase": "planning",
        "description": "基于已有 revision 创建新版本，不覆盖旧版本。",
    },
    {
        "name": "get_plan_revision",
        "phase": "planning",
        "description": "查询完整计划 revision 与任务树。",
    },
    {
        "name": "diff_plan_revisions",
        "phase": "planning",
        "description": "对比两个 revision 的结构变化。",
    },
    {
        "name": "approve_work_item",
        "phase": "review",
        "description": "批准 work item 并记录 review event。",
    },
    {
        "name": "reject_work_item",
        "phase": "review",
        "description": "驳回 work item 并记录 review event。",
    },
    {
        "name": "merge_work_items",
        "phase": "review",
        "description": "将多个 work item 合并到目标节点。",
    },
    {
        "name": "split_work_item",
        "phase": "review",
        "description": "拆分 work item，在其下新增子节点。",
    },
    {
        "name": "link_commit_to_work_item",
        "phase": "implementation",
        "description": "将 commit 或 PR 关联到 work item。",
    },
    {
        "name": "list_review_queue",
        "phase": "review",
        "description": "列出待审核的 work items。",
    },
]

RULE_TEMPLATE = """---
description: Enforce use of plan governor MCP for planning and replanning
globs:
alwaysApply: true
---

For any non-trivial feature request:
1. Do not start implementation immediately.
2. First call create_request.
3. Then call plan_feature to persist the initial plan tree.
4. If the user changes scope or asks to replan, call replan_feature and create a new revision.
5. Do not treat chat output as the only source of truth.
6. Before implementation, explicitly mention which approved revision is being executed.
7. During implementation, link commits/PRs via link_commit_to_work_item.
8. Use approve_work_item / reject_work_item / list_review_queue for governance.
"""


def _detect_project_root(project_root: str | None = None) -> Path:
    if project_root:
        return Path(project_root).resolve()
    return PROJECT_ROOT


def build_mcp_config(root: Path) -> dict:
    local_url = f"http://127.0.0.1:{get_mcp_port()}{get_mcp_http_path()}"
    config = {
        "mcpServers": {
            "plan-governor": build_stdio_mcp_entry(root, portable=True),
            "plan-governor-http": {
                "url": local_url,
            },
        }
    }

    lan_ip = get_lan_ip()
    if lan_ip:
        config["mcpServers"]["plan-governor-remote"] = {
            "url": build_mcp_http_url(host="0.0.0.0"),
        }

    return config


def build_setup_steps(root: Path) -> list[dict]:
    return [
        {
            "step": 1,
            "title": "安装依赖",
            "commands": [
                "python -m venv .venv",
                ".venv\\Scripts\\activate" if sys.platform == "win32" else "source .venv/bin/activate",
                'pip install -e ".[dev]"',
            ],
        },
        {
            "step": 2,
            "title": "配置 Cursor MCP",
            "action": f"创建或更新 {root / '.cursor' / 'mcp.json'}",
            "note": "使用返回的 mcp_config 内容；或在 Cursor Settings -> MCP -> Add new server 中粘贴。",
        },
        {
            "step": 3,
            "title": "启用 Rule 约束",
            "action": f"创建 {root / '.cursor' / 'rules' / 'plan-governance.mdc'}",
            "note": "使用返回的 rule_template 内容，确保复杂需求必须先持久化计划。",
        },
        {
            "step": 4,
            "title": "重启 Cursor 并验证 MCP",
            "action": "打开本项目，在 Cursor Settings -> MCP 确认 plan-governor 为 Connected。",
        },
        {
            "step": 5,
            "title": "验证全功能工作流",
            "workflow": [
                "create_request -> plan_feature -> list_review_queue",
                "approve_work_item / reject_work_item",
                "replan_feature -> diff_plan_revisions",
                "link_commit_to_work_item",
            ],
        },
    ]


def build_workflow_guide() -> dict:
    return {
        "new_feature": [
            "调用 create_request 创建需求",
            "调用 plan_feature 生成并持久化任务树",
            "向用户展示 plan_revision_id、任务树摘要与风险点",
            "调用 list_review_queue 列出待审项",
            "用户确认后调用 approve_work_item",
            "开始实现，并用 link_commit_to_work_item 回写证据",
        ],
        "replan": [
            "调用 get_plan_revision 获取当前 revision",
            "调用 replan_feature 创建新 revision（不可覆盖旧版）",
            "调用 diff_plan_revisions 说明变化",
        ],
        "review": [
            "调用 list_review_queue 获取待审队列",
            "使用 approve_work_item / reject_work_item 处理",
            "必要时使用 merge_work_items / split_work_item 调整结构",
        ],
    }


def render_setup_markdown(root: Path, mcp_config: dict) -> str:
    mcp_json = json.dumps(mcp_config, indent=2, ensure_ascii=False)
    lines = [
        "# Cursor Plan Governor 项目配置指南",
        "",
        f"项目根目录: `{root}`",
        "",
        "## 1. 安装依赖",
        "",
        "```bash",
        "python -m venv .venv",
        "pip install -e \".[dev]\"",
        "```",
        "",
        "## 2. Cursor MCP 配置",
        "",
        "在项目内创建 `.cursor/mcp.json`：",
        "",
        "```json",
        mcp_json,
        "```",
        "",
        "## 3. 启用 Rule",
        "",
        "创建 `.cursor/rules/plan-governance.mdc`，内容见 rule_template 字段。",
        "",
        "## 4. 全功能工作流",
        "",
        "### 新需求",
        "- create_request -> plan_feature -> list_review_queue -> approve_work_item",
        "",
        "### 重新规划",
        "- get_plan_revision -> replan_feature -> diff_plan_revisions",
        "",
        "### 开发闭环",
        "- link_commit_to_work_item 关联 commit/PR",
        "",
        "## 5. 验证",
        "",
        "在 Cursor MCP 面板确认 plan-governor 已连接，然后调用 create_request 做冒烟测试。",
    ]
    return "\n".join(lines)


def render_cursor_connection_log(project_root: Path | str | None = None) -> list[str]:
    """Return console lines describing how Cursor should connect to this MCP server."""
    root = Path(project_root).resolve() if project_root else Path.cwd().resolve()

    mcp_config = build_mcp_config(root)
    mcp_json_path = root / ".cursor" / "mcp.json"
    rule_path = root / ".cursor" / "rules" / "plan-governance.mdc"
    rule_status = "ok" if rule_path.is_file() else "missing (optional)"
    config_json = json.dumps(mcp_config, indent=2, ensure_ascii=False)

    lines = [
        "Cursor connection guide",
        "-----------------------",
        f"Config file: {mcp_json_path}",
        f"Rule file:   {rule_path} ({rule_status})",
        "",
        "Steps:",
        "  1. Use plan-governor below (launch_mcp_stdio.py picks .venv on Win/Linux).",
        "  2. Or start ./start-mcp-server.sh / start-mcp-server.bat for HTTP mode.",
        "  3. Ensure deps are installed: pip install -e \".[dev]\"",
        "  4. Open this project in Cursor.",
        "  5. Settings -> MCP -> confirm plan-governor is Connected.",
        "  6. Smoke test: ask Cursor to call create_request.",
        "",
        "Recommended .cursor/mcp.json:",
        config_json,
        "",
        "Full setup (rules, workflow, all options): call get_project_setup_guide.",
    ]
    return lines


def build_setup_guide(project_root: str | None = None) -> dict:
    root = _detect_project_root(project_root)
    mcp_config = build_mcp_config(root)

    return {
        "ok": True,
        "project_root": str(root),
        "platform": sys.platform,
        "mcp_config": mcp_config,
        "mcp_json_path": str(root / ".cursor" / "mcp.json"),
        "rule_template": RULE_TEMPLATE,
        "rule_path": str(root / ".cursor" / "rules" / "plan-governance.mdc"),
        "setup_steps": build_setup_steps(root),
        "workflow": build_workflow_guide(),
        "available_tools": ALL_TOOLS,
        "cursor_instructions": (
            "Follow setup_steps in order. Write mcp_config to .cursor/mcp.json and "
            "rule_template to .cursor/rules/plan-governance.mdc if they do not exist. "
            "After MCP shows Connected, use the full workflow: create_request, plan_feature, "
            "review tools, replan/diff, and link_commit_to_work_item."
        ),
        "markdown": render_setup_markdown(root, mcp_config),
    }
