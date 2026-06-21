# 建议 JSON Schema 草案

## create_request

```json
{
  "title": "实现登录错误处理治理",
  "source_type": "github_issue",
  "source_ref": "repo#123",
  "context_summary": "涉及前端 React 与后端 auth service"
}
```

## plan_feature

```json
{
  "request_id": "req_123",
  "goal": "统一登录错误处理",
  "summary": "首版计划",
  "context_summary": "修复错误码和展示不一致",
  "tree": [
    {
      "node_key": "1",
      "title": "梳理错误流",
      "description": "识别前后端错误处理链路",
      "children": [
        {
          "node_key": "1.1",
          "title": "梳理前端错误展示",
          "description": "识别 toast 与 inline error"
        },
        {
          "node_key": "1.2",
          "title": "统一错误码映射",
          "description": "后端错误码收敛"
        }
      ]
    }
  ]
}
```

