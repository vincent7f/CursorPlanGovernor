"""Minimal MCP server skeleton for Cursor Plan Governor.

This is a starter skeleton, not a production implementation.
Fill in repository logic and real MCP handlers in Cursor.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class InMemoryStore:
    def __init__(self) -> None:
        self.requests = {}
        self.revisions = {}
        self.work_items = {}

    def create_request(self, title: str, source_type: str | None, source_ref: str | None, context_summary: str | None):
        request_id = new_id("req")
        row = {
            "request_id": request_id,
            "title": title,
            "source_type": source_type,
            "source_ref": source_ref,
            "context_summary": context_summary,
            "created_at": now_iso(),
            "status": "open",
        }
        self.requests[request_id] = row
        return row

    def save_plan_revision(self, request_id: str, summary: str, tree: list[dict], based_on_revision_id: str | None = None):
        revision_id = new_id("planrev")
        revision_no = 1 + sum(1 for r in self.revisions.values() if r["request_id"] == request_id)
        revision = {
            "plan_revision_id": revision_id,
            "request_id": request_id,
            "revision_no": revision_no,
            "based_on_revision_id": based_on_revision_id,
            "summary": summary,
            "created_at": now_iso(),
            "status": "draft",
        }
        self.revisions[revision_id] = revision
        self.work_items[revision_id] = tree
        return revision


STORE = InMemoryStore()


def tool_create_request(arguments: dict) -> dict:
    row = STORE.create_request(
        title=arguments["title"],
        source_type=arguments.get("source_type"),
        source_ref=arguments.get("source_ref"),
        context_summary=arguments.get("context_summary"),
    )
    return {"ok": True, "request": row}


def tool_plan_feature(arguments: dict) -> dict:
    request_id = arguments["request_id"]
    goal = arguments["goal"]
    tree = arguments.get("tree") or [
        {
            "node_key": "1",
            "title": goal,
            "description": arguments.get("context_summary") or "",
            "children": [],
        }
    ]
    revision = STORE.save_plan_revision(
        request_id=request_id,
        summary=arguments.get("summary") or goal,
        tree=tree,
        based_on_revision_id=arguments.get("based_on_revision_id"),
    )
    markdown = f"# Plan Revision {revision['revision_no']}\n\n- request_id: {request_id}\n- revision_id: {revision['plan_revision_id']}\n- summary: {revision['summary']}\n"
    return {
        "ok": True,
        "plan_revision": revision,
        "tree": tree,
        "markdown": markdown,
    }


def tool_get_plan_revision(arguments: dict) -> dict:
    revision_id = arguments["plan_revision_id"]
    revision = STORE.revisions.get(revision_id)
    tree = STORE.work_items.get(revision_id, [])
    if not revision:
        return {"ok": False, "error": f"revision not found: {revision_id}"}
    return {"ok": True, "plan_revision": revision, "tree": tree}


def dispatch(method: str, arguments: dict) -> dict:
    if method == "create_request":
        return tool_create_request(arguments)
    if method == "plan_feature":
        return tool_plan_feature(arguments)
    if method == "get_plan_revision":
        return tool_get_plan_revision(arguments)
    return {"ok": False, "error": f"unknown method: {method}"}


# Note:
# This is a deliberately simple JSON-over-stdio dev skeleton, not a full MCP SDK server.
# Replace with proper MCP SDK implementation in Cursor.
def main() -> int:
    sys.stdout.write(json.dumps({
        "name": "cursor-plan-governor-dev",
        "mode": "skeleton",
        "message": "Replace this transport with a real MCP SDK server implementation."
    }) + "\n")
    sys.stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            method = req.get("method")
            arguments = req.get("arguments") or {}
            resp = dispatch(method, arguments)
        except Exception as exc:
            resp = {"ok": False, "error": str(exc)}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
