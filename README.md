# Cursor Plan Governor MCP Server

面向 Cursor 的 **MCP Server**，用于记录 Plan/任务拆分过程，支持任务树版本化、人工治理、以及 Commit/PR 关联。

## 功能

- 11 个 MCP Tool：`create_request`、`plan_feature`、`replan_feature`、`get_plan_revision`、`diff_plan_revisions`、`approve_work_item`、`reject_work_item`、`merge_work_items`、`split_work_item`、`link_commit_to_work_item`、`list_review_queue`
- SQLite 持久化（可通过环境变量切换数据库 URL）
- FastMCP（`mcp` 官方 SDK）stdio 传输

## 快速开始

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -e ".[dev]"
```

## 启动 MCP Server

```bash
python -m server.main
```

或使用 entry point：

```bash
plan-governor
```

## Cursor 配置

项目已包含 [`.cursor/mcp.json`](.cursor/mcp.json)。打开本项目后，在 Cursor Settings → MCP 中确认 `plan-governor` 已加载。

环境变量（可选）：

```text
PLAN_GOVERNOR_DB_URL=sqlite:///./plan_governor.db
```

## 测试

```bash
python -m pytest -v
```

## 文档

- [设计文档](docs/design.md)
- [安装与配置](docs/install-and-config.md)
- [Cursor 使用指引](docs/cursor-usage-guide.md)
- [Rule 示例](examples/plan-governance-rule.mdc)
- [Skill 大纲](examples/skill-outline.md)
