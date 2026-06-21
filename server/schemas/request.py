from __future__ import annotations

from pydantic import BaseModel, Field


class CreateRequestInput(BaseModel):
    title: str
    source_type: str | None = None
    source_ref: str | None = None
    context_summary: str | None = None


class RequestOutput(BaseModel):
    request_id: str
    title: str
    source_type: str | None = None
    source_ref: str | None = None
    context_summary: str | None = None
    created_at: str
    status: str
