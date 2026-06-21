# Cursor Plan Governor MCP Server 设计文档

## 1. 目标

该 MCP Server 的目标不是替代 Cursor 的编码能力，而是为 Cursor 提供一个外部、结构化、可治理的计划与任务树管理能力。

核心目标：

1. 记录需求的每次 Plan / Replan。
2. 保存任务树及子任务树的完整版本。
3. 支持人工 Review、修改、驳回、合并、拆分。
4. 将任务节点与 Commit / PR / Issue 建立映射。
5. 形成单一事实来源，避免计划信息散落在聊天记录、Markdown 和 PR 描述中。

## 2. 设计原则

- 第一性原理：系统的核心是“保存计划树演化事实”，而不是“再造一个任务系统”。
- Keep it simple and small：MVP 只做计划树、版本、审核、关联，不做复杂项目管理功能。
- 控制熵增：结构化数据统一落在 MCP 后端，Rule/Skill 只做约束与指引。
- 尽量复用成熟能力：Cursor 负责交互，PostgreSQL/SQLite 负责存储，GitHub/Linear 负责外部事实。

## 3. 推荐架构

```text
Cursor
  -> MCP Tools
      -> Plan Governor Server
          -> Storage (SQLite/PostgreSQL)
          -> Git Provider Adapter
          -> Issue Provider Adapter
```

### 3.1 分层职责

- Cursor Rule: 规定计划必须持久化、Replan 必须产生新版本。
- Cursor Skill: 指导如何拆任务、如何审核计划。
- MCP Server: 提供真实数据能力与持久化能力。
- DB: 保存 request、plan revision、work item、review event。

## 4. 领域模型

### 4.1 Request
原始需求入口，可映射 GitHub Issue / Linear Ticket / 自定义需求。

建议字段：
- request_id
- title
- source_type
- source_ref
- created_at
- status

### 4.2 PlanRevision
表示某次规划结果。

建议字段：
- plan_revision_id
- request_id
- revision_no
- based_on_revision_no
- created_at
- summary
- status

### 4.3 WorkItem
表示计划树节点，统一承载任务/子任务/子子任务。

建议字段：
- work_item_id
- request_id
- plan_revision_id
- node_key
- parent_node_key
- depth
- order_index
- title
- description
- risk
- status
- acceptance_criteria

### 4.4 ReviewEvent
记录人工治理动作。

建议字段：
- event_id
- request_id
- plan_revision_id
- work_item_id
- event_type
- actor_type
- actor_id
- event_time
- payload

## 5. MCP Tool 设计

MVP 建议至少实现以下 Tool：

1. `create_request`
2. `plan_feature`
3. `replan_feature`
4. `get_plan_revision`
5. `diff_plan_revisions`
6. `approve_work_item`
7. `reject_work_item`
8. `merge_work_items`
9. `split_work_item`
10. `link_commit_to_work_item`
11. `list_review_queue`

### 5.1 create_request
输入：title, source_type, source_ref, context_summary
输出：request_id

### 5.2 plan_feature
输入：request_id, goal, constraints, context_summary
输出：
- plan_revision_id
- structured task tree
- human readable markdown

### 5.3 replan_feature
输入：request_id, based_on_revision_id, changes, constraints
输出：新 revision

### 5.4 get_plan_revision
输入：request_id 或 plan_revision_id
输出：完整任务树

### 5.5 diff_plan_revisions
输入：base_revision, target_revision
输出：新增/删除/改名/移动/状态变化

### 5.6 approve_work_item / reject_work_item
输入：work_item_id, reviewer, comment
输出：review event id + 新状态

### 5.7 merge_work_items / split_work_item
用于人工治理过程中的结构修订。

### 5.8 link_commit_to_work_item
输入：work_item_id, repo, commit_sha 或 pr_ref
输出：关联记录

## 6. 数据存储建议

### 6.1 MVP
- 单人/小团队：SQLite
- 多人协作：PostgreSQL

### 6.2 最小表
- requests
- plan_revisions
- work_items
- review_events
- work_item_links

## 7. 版本策略

关键原则：**绝不覆盖旧 revision**。

每次 replan 必须新增一版计划树。旧版本保留用于审计、回放、比较与治理。

## 8. Cursor 集成建议

### 8.1 最小工作流

1. 用户描述需求。
2. Cursor 调用 `create_request`。
3. Cursor 调用 `plan_feature`。
4. 用户审核后，如需修改，Cursor 调用 `replan_feature`。
5. 用户确认后执行开发。
6. 开发完成时，将 commit / PR 通过 `link_commit_to_work_item` 回写。
7. 最后通过 `approve_work_item` 或批量验收完成闭环。

### 8.2 Rule 的职责

Rule 只做这些事情：
- 计划必须先持久化再执行。
- 不允许直接 build 未批准 revision。
- 每个 work item 必须有稳定编号。
- replan 不覆盖旧版本。

### 8.3 Skill 的职责

Skill 只做这些事情：
- 如何合理分层拆任务。
- 如何写 acceptance criteria。
- 如何做 review 和 merge/split。
- 如何控制过度拆分。

## 9. 安全与边界

- MCP Server 不直接执行危险 shell 命令。
- 所有写操作要有显式 tool 调用。
- 数据库写入需可审计。
- Git 链接默认只写元数据，不自动 push。

## 10. MVP 范围

第一版只建议实现：
- Request 创建
- Plan/Replan 持久化
- Revision 查询
- Work Item 审核
- Commit 关联
- Review Queue

不要一开始实现：
- 全自动代码执行编排
- 复杂权限系统
- 可视化大屏
- 多租户
- 深度 IDE 插件化 UI

## 11. 推荐开发顺序

1. 定义 JSON Schema
2. 实现 SQLite Repository
3. 实现 4 个核心 Tool：create_request / plan_feature / get_plan_revision / approve_work_item
4. 用 Cursor 接入 `.cursor/mcp.json`
5. 再补 replan / diff / link_commit

