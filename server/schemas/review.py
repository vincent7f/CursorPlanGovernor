from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewWorkItemInput(BaseModel):
    work_item_id: str
    reviewer: str
    comment: str | None = None


class MergeWorkItemsInput(BaseModel):
    target_work_item_id: str
    source_work_item_ids: list[str]
    reviewer: str
    comment: str | None = None
    merged_title: str | None = None
    merged_description: str | None = None


class SplitChildInput(BaseModel):
    node_key: str
    title: str
    description: str | None = None
    risk: str | None = None
    acceptance_criteria: str | None = None


class SplitWorkItemInput(BaseModel):
    work_item_id: str
    children: list[SplitChildInput]
    reviewer: str
    comment: str | None = None


class LinkCommitInput(BaseModel):
    work_item_id: str
    repo: str
    commit_sha: str | None = None
    pr_ref: str | None = None


class ListReviewQueueInput(BaseModel):
    request_id: str | None = None
    plan_revision_id: str | None = None


class ReviewEventOutput(BaseModel):
    event_id: str
    request_id: str
    plan_revision_id: str | None = None
    work_item_id: str | None = None
    event_type: str
    actor_type: str
    actor_id: str | None = None
    event_time: str
    payload: str | None = None


class WorkItemLinkOutput(BaseModel):
    link_id: str
    work_item_id: str
    link_type: str
    repo: str
    ref: str
    created_at: str


class WorkItemOutput(BaseModel):
    work_item_id: str
    request_id: str
    plan_revision_id: str
    node_key: str
    parent_node_key: str | None = None
    depth: int
    order_index: int
    title: str
    description: str | None = None
    risk: str | None = None
    status: str
    acceptance_criteria: str | None = None
