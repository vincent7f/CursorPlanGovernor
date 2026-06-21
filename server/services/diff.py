from __future__ import annotations

from server.schemas.plan import DiffEntry, DiffResult


def diff_plan_revisions(base_items: list, target_items: list) -> DiffResult:
    base_map = {item.node_key: item for item in base_items}
    target_map = {item.node_key: item for item in target_items}

    base_keys = set(base_map)
    target_keys = set(target_map)

    added: list[DiffEntry] = []
    removed: list[DiffEntry] = []
    renamed: list[DiffEntry] = []
    moved: list[DiffEntry] = []
    status_changed: list[DiffEntry] = []

    for key in sorted(target_keys - base_keys):
        item = target_map[key]
        added.append(
            DiffEntry(
                node_key=key,
                change_type="added",
                details={"title": item.title, "parent_node_key": item.parent_node_key},
            )
        )

    for key in sorted(base_keys - target_keys):
        item = base_map[key]
        removed.append(
            DiffEntry(
                node_key=key,
                change_type="removed",
                details={"title": item.title, "parent_node_key": item.parent_node_key},
            )
        )

    for key in sorted(base_keys & target_keys):
        base_item = base_map[key]
        target_item = target_map[key]

        if base_item.title != target_item.title:
            renamed.append(
                DiffEntry(
                    node_key=key,
                    change_type="renamed",
                    details={"from_title": base_item.title, "to_title": target_item.title},
                )
            )

        if base_item.parent_node_key != target_item.parent_node_key:
            moved.append(
                DiffEntry(
                    node_key=key,
                    change_type="moved",
                    details={
                        "from_parent": base_item.parent_node_key,
                        "to_parent": target_item.parent_node_key,
                    },
                )
            )

        if base_item.status != target_item.status:
            status_changed.append(
                DiffEntry(
                    node_key=key,
                    change_type="status_changed",
                    details={"from_status": base_item.status, "to_status": target_item.status},
                )
            )

    return DiffResult(
        added=added,
        removed=removed,
        renamed=renamed,
        moved=moved,
        status_changed=status_changed,
    )
