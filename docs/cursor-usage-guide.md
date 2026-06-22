# Cursor 使用指引

## 1. 目标

本指引用于告诉 Cursor 在真实使用中如何调用 Plan Governor MCP Server，而不是把计划仅保留在聊天里。

## 2. 推荐对话流程

### 场景：新需求

给 Cursor 的指令建议：

```text
这是一个新需求。先不要开始编码。
请先调用 create_request 创建需求，再调用 plan_feature 生成结构化计划树。
输出时同时给出：
1. plan revision id
2. 任务树摘要
3. 需要人工确认的风险点
```

### 场景：要求重新规划

```text
基于当前 revision 重新规划。
请调用 replan_feature，保留旧版本，不要覆盖。
说明新增、删除、重排了哪些节点。
```

### 场景：批准后进入开发

```text
使用已批准的 revision 继续执行。
开发过程中将实际实现的 commit 与对应 work item 关联。
```

## 3. 人工 Review 指引

建议人工重点检查：

- 是否过度拆分
- 是否遗漏关键风险
- 子任务边界是否清晰
- acceptance criteria 是否可验证
- 是否有无意义的“工程化噪音”节点

## 4. 最小约束模板

建议把以下内容放入 rule 或作为对话模板：

```text
对于复杂需求，必须先通过 MCP server 持久化计划树，再进入实现阶段。
任何 replan 必须形成新 revision。
不得只在聊天中保留唯一版本的计划。
```

