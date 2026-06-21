from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Request(Base):
    __tablename__ = "requests"

    request_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    context_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    status: Mapped[str] = mapped_column(String(32), default="open")

    plan_revisions: Mapped[list[PlanRevision]] = relationship(back_populates="request")


class PlanRevision(Base):
    __tablename__ = "plan_revisions"

    plan_revision_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.request_id"), nullable=False)
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    based_on_revision_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    status: Mapped[str] = mapped_column(String(32), default="draft")

    request: Mapped[Request] = relationship(back_populates="plan_revisions")
    work_items: Mapped[list[WorkItem]] = relationship(back_populates="plan_revision")

    __table_args__ = (
        UniqueConstraint("request_id", "revision_no", name="uq_request_revision_no"),
    )


class WorkItem(Base):
    __tablename__ = "work_items"

    work_item_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.request_id"), nullable=False)
    plan_revision_id: Mapped[str] = mapped_column(
        ForeignKey("plan_revisions.plan_revision_id"), nullable=False
    )
    node_key: Mapped[str] = mapped_column(String(64), nullable=False)
    parent_node_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending_review")
    acceptance_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)

    plan_revision: Mapped[PlanRevision] = relationship(back_populates="work_items")

    __table_args__ = (
        UniqueConstraint("plan_revision_id", "node_key", name="uq_revision_node_key"),
    )


class ReviewEvent(Base):
    __tablename__ = "review_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.request_id"), nullable=False)
    plan_revision_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    work_item_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(32), default="human")
    actor_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)


class WorkItemLink(Base):
    __tablename__ = "work_item_links"

    link_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    work_item_id: Mapped[str] = mapped_column(ForeignKey("work_items.work_item_id"), nullable=False)
    link_type: Mapped[str] = mapped_column(String(32), nullable=False)
    repo: Mapped[str] = mapped_column(String(512), nullable=False)
    ref: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
