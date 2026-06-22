"""Cursor Plan Governor MCP Server."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from server.db.repository import PlanGovernorRepository
from server.db.session import get_session_factory, init_db
from server.schemas.plan import TreeNodeInput
from server.services.diff import diff_plan_revisions
from server.services.markdown import render_plan_markdown
from server.services.setup_guide import build_setup_guide

mcp = FastMCP("plan-governor")


@contextmanager
def get_repo():
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield PlanGovernorRepository(session)
    finally:
        session.close()


def _tree_nodes(raw_tree: list[dict] | None) -> list[TreeNodeInput]:
    if not raw_tree:
        return []

    def convert(node: dict) -> TreeNodeInput:
        children = [_tree_nodes([child])[0] for child in node.get("children", [])]
        return TreeNodeInput(
            node_key=node["node_key"],
            title=node["title"],
            description=node.get("description"),
            risk=node.get("risk"),
            acceptance_criteria=node.get("acceptance_criteria"),
            children=children,
        )

    return [convert(node) for node in raw_tree]


def _tree_output(tree) -> list[dict]:
    return [node.model_dump() for node in tree]


def _error(message: str) -> dict[str, Any]:
    return {"ok": False, "error": message}


@mcp.tool()
def get_project_setup_guide(project_root: str | None = None) -> dict:
    """Return step-by-step instructions for configuring Cursor to connect to this MCP server and enable all plan governance features."""
    return build_setup_guide(project_root=project_root)


@mcp.tool()
def create_request(
    title: str,
    source_type: str | None = None,
    source_ref: str | None = None,
    context_summary: str | None = None,
) -> dict:
    """Create a new planning request entry."""
    with get_repo() as repo:
        row = repo.create_request(
            title=title,
            source_type=source_type,
            source_ref=source_ref,
            context_summary=context_summary,
        )
        return {"ok": True, "request": repo.request_to_dict(row)}


@mcp.tool()
def plan_feature(
    request_id: str,
    goal: str,
    summary: str | None = None,
    context_summary: str | None = None,
    tree: list[dict] | None = None,
) -> dict:
    """Create the initial plan revision and persist the task tree."""
    with get_repo() as repo:
        if repo.get_request(request_id) is None:
            return _error(f"request not found: {request_id}")

        nodes = _tree_nodes(tree)
        if not nodes:
            nodes = [
                TreeNodeInput(
                    node_key="1",
                    title=goal,
                    description=context_summary or "",
                    children=[],
                )
            ]

        revision, output_tree = repo.save_plan_revision(
            request_id=request_id,
            summary=summary or goal,
            tree=nodes,
        )
        revision_dict = repo.revision_to_dict(revision)
        markdown = render_plan_markdown(revision_dict, output_tree)
        return {
            "ok": True,
            "plan_revision": revision_dict,
            "tree": _tree_output(output_tree),
            "markdown": markdown,
        }


@mcp.tool()
def replan_feature(
    request_id: str,
    based_on_revision_id: str,
    tree: list[dict],
    changes: str | None = None,
    constraints: str | None = None,
    summary: str | None = None,
) -> dict:
    """Create a new plan revision based on an existing one without overwriting it."""
    with get_repo() as repo:
        if repo.get_request(request_id) is None:
            return _error(f"request not found: {request_id}")

        base_revision = repo.get_plan_revision(based_on_revision_id)
        if base_revision is None:
            return _error(f"revision not found: {based_on_revision_id}")
        if base_revision.request_id != request_id:
            return _error("based_on_revision_id does not belong to request_id")

        nodes = _tree_nodes(tree)
        if not nodes:
            return _error("tree is required for replan_feature")

        revision_summary = summary or changes or f"Replan based on {based_on_revision_id}"
        revision, output_tree = repo.save_plan_revision(
            request_id=request_id,
            summary=revision_summary,
            tree=nodes,
            based_on_revision_id=based_on_revision_id,
        )
        revision_dict = repo.revision_to_dict(revision)
        markdown = render_plan_markdown(revision_dict, output_tree)
        return {
            "ok": True,
            "plan_revision": revision_dict,
            "tree": _tree_output(output_tree),
            "markdown": markdown,
            "constraints": constraints,
        }


@mcp.tool()
def get_plan_revision(
    plan_revision_id: str | None = None,
    request_id: str | None = None,
) -> dict:
    """Get a full plan revision and its task tree."""
    if not plan_revision_id and not request_id:
        return _error("plan_revision_id or request_id is required")

    with get_repo() as repo:
        revision = None
        if plan_revision_id:
            revision = repo.get_plan_revision(plan_revision_id)
        elif request_id:
            revision = repo.get_latest_revision(request_id)

        if revision is None:
            return _error("plan revision not found")

        tree = repo.get_tree_for_revision(revision.plan_revision_id)
        return {
            "ok": True,
            "plan_revision": repo.revision_to_dict(revision),
            "tree": _tree_output(tree),
        }


@mcp.tool()
def diff_plan_revisions(base_revision_id: str, target_revision_id: str) -> dict:
    """Compare two plan revisions and report structural changes."""
    with get_repo() as repo:
        base_revision = repo.get_plan_revision(base_revision_id)
        target_revision = repo.get_plan_revision(target_revision_id)
        if base_revision is None:
            return _error(f"base revision not found: {base_revision_id}")
        if target_revision is None:
            return _error(f"target revision not found: {target_revision_id}")

        base_items = repo.get_work_items_for_revision(base_revision_id)
        target_items = repo.get_work_items_for_revision(target_revision_id)
        diff = diff_plan_revisions(base_items, target_items)
        return {"ok": True, "diff": diff.model_dump()}


@mcp.tool()
def approve_work_item(
    work_item_id: str,
    reviewer: str,
    comment: str | None = None,
) -> dict:
    """Approve a work item and record a review event."""
    with get_repo() as repo:
        try:
            item, event = repo.approve_work_item(work_item_id, reviewer, comment)
        except ValueError as exc:
            return _error(str(exc))
        return {
            "ok": True,
            "work_item": repo.work_item_to_dict(item),
            "review_event": repo.review_event_to_dict(event),
        }


@mcp.tool()
def reject_work_item(
    work_item_id: str,
    reviewer: str,
    comment: str | None = None,
) -> dict:
    """Reject a work item and record a review event."""
    with get_repo() as repo:
        try:
            item, event = repo.reject_work_item(work_item_id, reviewer, comment)
        except ValueError as exc:
            return _error(str(exc))
        return {
            "ok": True,
            "work_item": repo.work_item_to_dict(item),
            "review_event": repo.review_event_to_dict(event),
        }


@mcp.tool()
def merge_work_items(
    target_work_item_id: str,
    source_work_item_ids: list[str],
    reviewer: str,
    comment: str | None = None,
    merged_title: str | None = None,
    merged_description: str | None = None,
) -> dict:
    """Merge multiple work items into a target work item."""
    with get_repo() as repo:
        try:
            item, event = repo.merge_work_items(
                target_work_item_id=target_work_item_id,
                source_work_item_ids=source_work_item_ids,
                reviewer=reviewer,
                comment=comment,
                merged_title=merged_title,
                merged_description=merged_description,
            )
        except ValueError as exc:
            return _error(str(exc))
        return {
            "ok": True,
            "work_item": repo.work_item_to_dict(item),
            "review_event": repo.review_event_to_dict(event),
        }


@mcp.tool()
def split_work_item(
    work_item_id: str,
    children: list[dict],
    reviewer: str,
    comment: str | None = None,
) -> dict:
    """Split a work item by adding child nodes under it."""
    with get_repo() as repo:
        try:
            created, event = repo.split_work_item(
                work_item_id=work_item_id,
                children=children,
                reviewer=reviewer,
                comment=comment,
            )
        except ValueError as exc:
            return _error(str(exc))
        return {
            "ok": True,
            "children": [repo.work_item_to_dict(row) for row in created],
            "review_event": repo.review_event_to_dict(event),
        }


@mcp.tool()
def link_commit_to_work_item(
    work_item_id: str,
    repo: str,
    commit_sha: str | None = None,
    pr_ref: str | None = None,
) -> dict:
    """Link a commit or PR reference to a work item."""
    with get_repo() as repo_obj:
        try:
            link = repo_obj.link_commit_to_work_item(
                work_item_id=work_item_id,
                repo=repo,
                commit_sha=commit_sha,
                pr_ref=pr_ref,
            )
        except ValueError as exc:
            return _error(str(exc))
        return {"ok": True, "link": repo_obj.link_to_dict(link)}


@mcp.tool()
def list_review_queue(
    request_id: str | None = None,
    plan_revision_id: str | None = None,
) -> dict:
    """List work items that are pending review."""
    with get_repo() as repo:
        items = repo.list_review_queue(
            request_id=request_id,
            plan_revision_id=plan_revision_id,
        )
        return {
            "ok": True,
            "items": [repo.work_item_to_dict(item) for item in items],
            "count": len(items),
        }


def main() -> None:
    init_db()
    mcp.run()


if __name__ == "__main__":
    main()
