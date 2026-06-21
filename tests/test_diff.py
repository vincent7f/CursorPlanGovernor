from __future__ import annotations

from server.services.diff import diff_plan_revisions


def test_diff_added_removed_moved():
    class Item:
        def __init__(self, node_key, title, parent_node_key=None, status="pending_review"):
            self.node_key = node_key
            self.title = title
            self.parent_node_key = parent_node_key
            self.status = status

    base = [
        Item("1", "Root"),
        Item("1.1", "Child A", "1"),
    ]
    target = [
        Item("1", "Root"),
        Item("1.2", "Child B", "1"),
        Item("2", "New root"),
    ]

    result = diff_plan_revisions(base, target)
    assert {entry.node_key for entry in result.added} == {"1.2", "2"}
    assert {entry.node_key for entry in result.removed} == {"1.1"}


def test_diff_renamed_and_status_changed():
    class Item:
        def __init__(self, node_key, title, parent_node_key=None, status="pending_review"):
            self.node_key = node_key
            self.title = title
            self.parent_node_key = parent_node_key
            self.status = status

    base = [Item("1", "Old title", status="pending_review")]
    target = [Item("1", "New title", status="approved")]

    result = diff_plan_revisions(base, target)
    assert len(result.renamed) == 1
    assert result.renamed[0].node_key == "1"
    assert len(result.status_changed) == 1
