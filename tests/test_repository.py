from __future__ import annotations

import pytest

from server.db.repository import PlanGovernorRepository
from server.db.session import get_session_factory, init_db, reset_engine
from server.schemas.plan import TreeNodeInput


@pytest.fixture
def repo():
    reset_engine()
    init_db("sqlite:///:memory:")
    session = get_session_factory("sqlite:///:memory:")()
    repository = PlanGovernorRepository(session)
    yield repository
    session.close()
    reset_engine()


def test_create_request_and_plan(repo: PlanGovernorRepository):
    request = repo.create_request(title="Login error handling")
    assert request.request_id.startswith("req_")

    tree = [
        TreeNodeInput(
            node_key="1",
            title="Analyze flow",
            children=[
                TreeNodeInput(node_key="1.1", title="Frontend"),
            ],
        )
    ]
    revision, output_tree = repo.save_plan_revision(
        request_id=request.request_id,
        summary="Initial plan",
        tree=tree,
    )
    assert revision.revision_no == 1
    assert len(output_tree) == 1
    assert len(output_tree[0].children) == 1

    revision2, _ = repo.save_plan_revision(
        request_id=request.request_id,
        summary="Replan",
        tree=tree,
        based_on_revision_id=revision.plan_revision_id,
    )
    assert revision2.revision_no == 2
    assert revision2.based_on_revision_id == revision.plan_revision_id


def test_review_and_link(repo: PlanGovernorRepository):
    request = repo.create_request(title="Feature")
    tree = [TreeNodeInput(node_key="1", title="Task")]
    _, output_tree = repo.save_plan_revision(
        request_id=request.request_id,
        summary="Plan",
        tree=tree,
    )
    work_item_id = output_tree[0].work_item_id
    assert work_item_id is not None

    item, event = repo.approve_work_item(work_item_id, reviewer="alice", comment="LGTM")
    assert item.status == "approved"
    assert event.event_type == "approve"

    link = repo.link_commit_to_work_item(
        work_item_id=work_item_id,
        repo="org/repo",
        commit_sha="abc123",
    )
    assert link.link_type == "commit"
    assert link.ref == "abc123"

    pending = repo.list_review_queue(request_id=request.request_id)
    assert pending == []
