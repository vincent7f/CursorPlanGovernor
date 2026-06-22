from __future__ import annotations

import pytest

from server.db.repository import PlanGovernorRepository
from server.db.session import get_session_factory, init_db, reset_engine
from server.schemas.plan import TreeNodeInput
from server.services.tree import flatten_tree, rebuild_tree


@pytest.fixture
def repo():
    reset_engine()
    init_db("sqlite:///:memory:")
    session = get_session_factory("sqlite:///:memory:")()
    repository = PlanGovernorRepository(session)
    yield repository
    session.close()
    reset_engine()


SAMPLE_TREE = [
    TreeNodeInput(
        node_key="1",
        title="Root",
        description="root task",
        children=[
            TreeNodeInput(
                node_key="1.1",
                title="Child A",
                description="first child",
            ),
            TreeNodeInput(
                node_key="1.2",
                title="Child B",
                description="second child",
            ),
        ],
    )
]


def test_flatten_and_rebuild_roundtrip():
    flat = flatten_tree(SAMPLE_TREE, "req_1", "rev_1")
    assert len(flat) == 3
    assert flat[0]["node_key"] == "1"
    assert flat[0]["depth"] == 0
    assert flat[1]["parent_node_key"] == "1"
    assert flat[1]["depth"] == 1

    class Row:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    rows = [
        Row(
            node_key=item["node_key"],
            title=item["title"],
            description=item.get("description"),
            parent_node_key=item.get("parent_node_key"),
            status=item.get("status"),
            acceptance_criteria=item.get("acceptance_criteria"),
            work_item_id=f"wi_{item['node_key']}",
        )
        for item in flat
    ]
    rebuilt = rebuild_tree(rows)
    assert len(rebuilt) == 1
    assert rebuilt[0].node_key == "1"
    assert len(rebuilt[0].children) == 2
    assert rebuilt[0].children[0].node_key == "1.1"
