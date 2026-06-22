from __future__ import annotations

from pydantic import BaseModel, Field


class TreeNodeInput(BaseModel):
    node_key: str
    title: str
    description: str | None = None
    risk: str | None = None
    acceptance_criteria: str | None = None
    children: list[TreeNodeInput] = Field(default_factory=list)


class TreeNodeOutput(BaseModel):
    node_key: str
    title: str
    description: str | None = None
    risk: str | None = None
    status: str | None = None
    acceptance_criteria: str | None = None
    work_item_id: str | None = None
    children: list[TreeNodeOutput] = Field(default_factory=list)


class PlanFeatureInput(BaseModel):
    request_id: str
    goal: str
    summary: str | None = None
    context_summary: str | None = None
    tree: list[TreeNodeInput] | None = None


class ReplanFeatureInput(BaseModel):
    request_id: str
    based_on_revision_id: str
    changes: str | None = None
    constraints: str | None = None
    summary: str | None = None
    tree: list[TreeNodeInput]


class PlanRevisionOutput(BaseModel):
    plan_revision_id: str
    request_id: str
    revision_no: int
    based_on_revision_id: str | None = None
    summary: str
    created_at: str
    status: str


class GetPlanRevisionInput(BaseModel):
    plan_revision_id: str | None = None
    request_id: str | None = None


class DiffPlanRevisionsInput(BaseModel):
    base_revision_id: str
    target_revision_id: str


class DiffEntry(BaseModel):
    node_key: str
    change_type: str
    details: dict = Field(default_factory=dict)


class DiffResult(BaseModel):
    added: list[DiffEntry] = Field(default_factory=list)
    removed: list[DiffEntry] = Field(default_factory=list)
    renamed: list[DiffEntry] = Field(default_factory=list)
    moved: list[DiffEntry] = Field(default_factory=list)
    status_changed: list[DiffEntry] = Field(default_factory=list)
