from __future__ import annotations

from server.schemas.plan import TreeNodeInput, TreeNodeOutput


def flatten_tree(
    tree: list[TreeNodeInput],
    request_id: str,
    plan_revision_id: str,
    parent_node_key: str | None = None,
    depth: int = 0,
) -> list[dict]:
    flat: list[dict] = []
    for order_index, node in enumerate(tree):
        flat.append(
            {
                "request_id": request_id,
                "plan_revision_id": plan_revision_id,
                "node_key": node.node_key,
                "parent_node_key": parent_node_key,
                "depth": depth,
                "order_index": order_index,
                "title": node.title,
                "description": node.description,
                "risk": node.risk,
                "status": "pending_review",
                "acceptance_criteria": node.acceptance_criteria,
            }
        )
        if node.children:
            flat.extend(
                flatten_tree(
                    node.children,
                    request_id,
                    plan_revision_id,
                    parent_node_key=node.node_key,
                    depth=depth + 1,
                )
            )
    return flat


def rebuild_tree(rows: list) -> list[TreeNodeOutput]:
    nodes_by_key: dict[str, TreeNodeOutput] = {}
    roots: list[TreeNodeOutput] = []

    for row in rows:
        node = TreeNodeOutput(
            node_key=row.node_key,
            title=row.title,
            description=getattr(row, "description", None),
            risk=getattr(row, "risk", None),
            status=getattr(row, "status", None),
            acceptance_criteria=getattr(row, "acceptance_criteria", None),
            work_item_id=getattr(row, "work_item_id", None),
            children=[],
        )
        nodes_by_key[row.node_key] = node

    for row in rows:
        node = nodes_by_key[row.node_key]
        parent_key = getattr(row, "parent_node_key", None)
        if parent_key and parent_key in nodes_by_key:
            nodes_by_key[parent_key].children.append(node)
        else:
            roots.append(node)

    return roots
