from __future__ import annotations

from server.schemas.plan import TreeNodeOutput


def render_plan_markdown(revision: dict, tree: list[TreeNodeOutput]) -> str:
    lines = [
        f"# Plan Revision {revision['revision_no']}",
        "",
        f"- request_id: {revision['request_id']}",
        f"- revision_id: {revision['plan_revision_id']}",
        f"- summary: {revision['summary']}",
        f"- status: {revision['status']}",
        "",
        "## Task Tree",
        "",
    ]

    def render_nodes(nodes: list[TreeNodeOutput], indent: int = 0) -> None:
        for node in nodes:
            prefix = "  " * indent
            status = f" [{node.status}]" if node.status else ""
            lines.append(f"{prefix}- {node.node_key} {node.title}{status}")
            if node.description:
                lines.append(f"{prefix}  {node.description}")
            if node.acceptance_criteria:
                lines.append(f"{prefix}  AC: {node.acceptance_criteria}")
            if node.children:
                render_nodes(node.children, indent + 1)

    render_nodes(tree)
    return "\n".join(lines)
