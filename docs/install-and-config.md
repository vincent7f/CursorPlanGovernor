# 安装与配置指引

## 1. 环境要求

- Python 3.11+
- Cursor（支持 MCP）
- 可选：SQLite 或 PostgreSQL

## 2. 目录建议

```text
cursor-plan-governor/
  server/
  docs/
  examples/
  .cursor/
```

## 3. 安装依赖

建议在项目内创建虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install mcp pydantic sqlalchemy
```

如果你打算先做最小原型，可暂时只安装：

```bash
pip install mcp pydantic
```

## 4. 启动方式

本包默认采用 **STDIO MCP Server** 方式，因为它最适合本地开发与 Cursor 集成。

Cursor 文档说明，STDIO 类型的 MCP Server 需要在 `mcp.json` 中至少配置 `type`、`command`，并可配置 `args`、`env`、`envFile`。[web:60][web:50]

## 5. Cursor 项目级配置

在你的项目内创建：

```text
.cursor/mcp.json
```

示例：

```json
{
  "mcpServers": {
    "plan-governor": {
      "type": "stdio",
      "command": "python",
      "args": [
        "./server/main.py"
      ],
      "env": {
        "PLAN_GOVERNOR_DB_URL": "sqlite:///./plan_governor.db"
      }
    }
  }
}
```

Cursor 文档同时说明，项目专用工具可放在项目下的 `.cursor/mcp.json`，全局工具可放在 `~/.cursor/mcp.json`。[web:50][web:64]

## 6. 在 Cursor 中启用

可通过两种方式：

1. 图形界面：Cursor Settings -> MCP -> Add new server。
2. 手工方式：直接编辑 `.cursor/mcp.json` 或 `~/.cursor/mcp.json`。[web:61][web:69][web:72]

## 7. 推荐 Rule 配合

建议额外加入一个 rule，约束 Cursor：

- 开始规划前必须调用 `create_request`
- 完成规划后必须调用 `plan_feature`
- Replan 必须调用 `replan_feature`
- 未经确认不得直接进入 build

## 8. 最小验证步骤

1. 启动 Cursor 并打开项目。
2. 确认 MCP server 成功加载。
3. 在对话中要求 Cursor 调用 `create_request`。
4. 再要求其调用 `plan_feature` 生成首版计划。
5. 检查数据库或日志中是否已保存 request 和 revision。

## 9. 后续扩展

当 MVP 跑通后，再逐步增加：

- PostgreSQL 支持
- GitHub / Linear Adapter
- diff_plan_revisions
- 批量审批
- Web Review UI

