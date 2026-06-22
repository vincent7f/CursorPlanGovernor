from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from server.db.models import PlanRevision, Request, ReviewEvent, WorkItem, WorkItemLink
from server.schemas.plan import TreeNodeInput, TreeNodeOutput
from server.services.tree import flatten_tree, rebuild_tree


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


class PlanGovernorRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_request(
        self,
        title: str,
        source_type: str | None = None,
        source_ref: str | None = None,
        context_summary: str | None = None,
    ) -> Request:
        row = Request(
            request_id=new_id("req"),
            title=title,
            source_type=source_type,
            source_ref=source_ref,
            context_summary=context_summary,
            status="open",
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def get_request(self, request_id: str) -> Request | None:
        return self.session.get(Request, request_id)

    def request_to_dict(self, row: Request) -> dict:
        return {
            "request_id": row.request_id,
            "title": row.title,
            "source_type": row.source_type,
            "source_ref": row.source_ref,
            "context_summary": row.context_summary,
            "created_at": _iso(row.created_at),
            "status": row.status,
        }

    def _next_revision_no(self, request_id: str) -> int:
        max_no = (
            self.session.query(func.max(PlanRevision.revision_no))
            .filter(PlanRevision.request_id == request_id)
            .scalar()
        )
        return (max_no or 0) + 1

    def save_plan_revision(
        self,
        request_id: str,
        summary: str,
        tree: list[TreeNodeInput],
        based_on_revision_id: str | None = None,
    ) -> tuple[PlanRevision, list[TreeNodeOutput]]:
        request = self.get_request(request_id)
        if request is None:
            raise ValueError(f"request not found: {request_id}")

        revision = PlanRevision(
            plan_revision_id=new_id("planrev"),
            request_id=request_id,
            revision_no=self._next_revision_no(request_id),
            based_on_revision_id=based_on_revision_id,
            summary=summary,
            status="draft",
        )
        self.session.add(revision)
        self.session.flush()

        flat_items = flatten_tree(tree, request_id, revision.plan_revision_id)
        work_item_rows: list[WorkItem] = []
        for item in flat_items:
            row = WorkItem(
                work_item_id=new_id("wi"),
                request_id=item["request_id"],
                plan_revision_id=item["plan_revision_id"],
                node_key=item["node_key"],
                parent_node_key=item["parent_node_key"],
                depth=item["depth"],
                order_index=item["order_index"],
                title=item["title"],
                description=item.get("description"),
                risk=item.get("risk"),
                status=item.get("status", "pending_review"),
                acceptance_criteria=item.get("acceptance_criteria"),
            )
            work_item_rows.append(row)
            self.session.add(row)

        self.session.commit()
        self.session.refresh(revision)

        output_tree = rebuild_tree(work_item_rows)
        return revision, output_tree

    def get_plan_revision(self, plan_revision_id: str) -> PlanRevision | None:
        return self.session.get(PlanRevision, plan_revision_id)

    def get_latest_revision(self, request_id: str) -> PlanRevision | None:
        return (
            self.session.query(PlanRevision)
            .filter(PlanRevision.request_id == request_id)
            .order_by(desc(PlanRevision.revision_no))
            .first()
        )

    def revision_to_dict(self, row: PlanRevision) -> dict:
        return {
            "plan_revision_id": row.plan_revision_id,
            "request_id": row.request_id,
            "revision_no": row.revision_no,
            "based_on_revision_id": row.based_on_revision_id,
            "summary": row.summary,
            "created_at": _iso(row.created_at),
            "status": row.status,
        }

    def get_work_items_for_revision(self, plan_revision_id: str) -> list[WorkItem]:
        return (
            self.session.query(WorkItem)
            .filter(WorkItem.plan_revision_id == plan_revision_id)
            .order_by(WorkItem.depth, WorkItem.order_index, WorkItem.node_key)
            .all()
        )

    def get_tree_for_revision(self, plan_revision_id: str) -> list[TreeNodeOutput]:
        rows = self.get_work_items_for_revision(plan_revision_id)
        return rebuild_tree(rows)

    def get_work_item(self, work_item_id: str) -> WorkItem | None:
        return self.session.get(WorkItem, work_item_id)

    def work_item_to_dict(self, row: WorkItem) -> dict:
        return {
            "work_item_id": row.work_item_id,
            "request_id": row.request_id,
            "plan_revision_id": row.plan_revision_id,
            "node_key": row.node_key,
            "parent_node_key": row.parent_node_key,
            "depth": row.depth,
            "order_index": row.order_index,
            "title": row.title,
            "description": row.description,
            "risk": row.risk,
            "status": row.status,
            "acceptance_criteria": row.acceptance_criteria,
        }

    def _create_review_event(
        self,
        request_id: str,
        event_type: str,
        plan_revision_id: str | None = None,
        work_item_id: str | None = None,
        actor_id: str | None = None,
        payload: dict | None = None,
    ) -> ReviewEvent:
        event = ReviewEvent(
            event_id=new_id("rev"),
            request_id=request_id,
            plan_revision_id=plan_revision_id,
            work_item_id=work_item_id,
            event_type=event_type,
            actor_type="human",
            actor_id=actor_id,
            payload=json.dumps(payload, ensure_ascii=False) if payload else None,
        )
        self.session.add(event)
        return event

    def review_event_to_dict(self, row: ReviewEvent) -> dict:
        return {
            "event_id": row.event_id,
            "request_id": row.request_id,
            "plan_revision_id": row.plan_revision_id,
            "work_item_id": row.work_item_id,
            "event_type": row.event_type,
            "actor_type": row.actor_type,
            "actor_id": row.actor_id,
            "event_time": _iso(row.event_time),
            "payload": row.payload,
        }

    def approve_work_item(
        self, work_item_id: str, reviewer: str, comment: str | None = None
    ) -> tuple[WorkItem, ReviewEvent]:
        item = self.get_work_item(work_item_id)
        if item is None:
            raise ValueError(f"work item not found: {work_item_id}")
        item.status = "approved"
        event = self._create_review_event(
            request_id=item.request_id,
            plan_revision_id=item.plan_revision_id,
            work_item_id=work_item_id,
            event_type="approve",
            actor_id=reviewer,
            payload={"comment": comment} if comment else None,
        )
        self.session.commit()
        self.session.refresh(item)
        self.session.refresh(event)
        return item, event

    def reject_work_item(
        self, work_item_id: str, reviewer: str, comment: str | None = None
    ) -> tuple[WorkItem, ReviewEvent]:
        item = self.get_work_item(work_item_id)
        if item is None:
            raise ValueError(f"work item not found: {work_item_id}")
        item.status = "rejected"
        event = self._create_review_event(
            request_id=item.request_id,
            plan_revision_id=item.plan_revision_id,
            work_item_id=work_item_id,
            event_type="reject",
            actor_id=reviewer,
            payload={"comment": comment} if comment else None,
        )
        self.session.commit()
        self.session.refresh(item)
        self.session.refresh(event)
        return item, event

    def merge_work_items(
        self,
        target_work_item_id: str,
        source_work_item_ids: list[str],
        reviewer: str,
        comment: str | None = None,
        merged_title: str | None = None,
        merged_description: str | None = None,
    ) -> tuple[WorkItem, ReviewEvent]:
        target = self.get_work_item(target_work_item_id)
        if target is None:
            raise ValueError(f"target work item not found: {target_work_item_id}")

        sources: list[WorkItem] = []
        for source_id in source_work_item_ids:
            source = self.get_work_item(source_id)
            if source is None:
                raise ValueError(f"source work item not found: {source_id}")
            if source.plan_revision_id != target.plan_revision_id:
                raise ValueError("all work items must belong to the same revision")
            sources.append(source)

        if merged_title:
            target.title = merged_title
        if merged_description:
            target.description = merged_description

        for source in sources:
            source.status = "merged"

        event = self._create_review_event(
            request_id=target.request_id,
            plan_revision_id=target.plan_revision_id,
            work_item_id=target_work_item_id,
            event_type="merge",
            actor_id=reviewer,
            payload={
                "comment": comment,
                "source_work_item_ids": source_work_item_ids,
            },
        )
        self.session.commit()
        self.session.refresh(target)
        self.session.refresh(event)
        return target, event

    def split_work_item(
        self,
        work_item_id: str,
        children: list[dict],
        reviewer: str,
        comment: str | None = None,
    ) -> tuple[list[WorkItem], ReviewEvent]:
        parent = self.get_work_item(work_item_id)
        if parent is None:
            raise ValueError(f"work item not found: {work_item_id}")

        existing_keys = {
            row.node_key
            for row in self.get_work_items_for_revision(parent.plan_revision_id)
        }
        created: list[WorkItem] = []
        for idx, child in enumerate(children):
            node_key = child["node_key"]
            if node_key in existing_keys:
                raise ValueError(f"node_key already exists: {node_key}")
            row = WorkItem(
                work_item_id=new_id("wi"),
                request_id=parent.request_id,
                plan_revision_id=parent.plan_revision_id,
                node_key=node_key,
                parent_node_key=parent.node_key,
                depth=parent.depth + 1,
                order_index=idx,
                title=child["title"],
                description=child.get("description"),
                risk=child.get("risk"),
                status="pending_review",
                acceptance_criteria=child.get("acceptance_criteria"),
            )
            created.append(row)
            self.session.add(row)
            existing_keys.add(node_key)

        event = self._create_review_event(
            request_id=parent.request_id,
            plan_revision_id=parent.plan_revision_id,
            work_item_id=work_item_id,
            event_type="split",
            actor_id=reviewer,
            payload={"comment": comment, "children": [c["node_key"] for c in children]},
        )
        self.session.commit()
        for row in created:
            self.session.refresh(row)
        self.session.refresh(event)
        return created, event

    def link_commit_to_work_item(
        self,
        work_item_id: str,
        repo: str,
        commit_sha: str | None = None,
        pr_ref: str | None = None,
    ) -> WorkItemLink:
        item = self.get_work_item(work_item_id)
        if item is None:
            raise ValueError(f"work item not found: {work_item_id}")
        if not commit_sha and not pr_ref:
            raise ValueError("commit_sha or pr_ref is required")
        if commit_sha and pr_ref:
            raise ValueError("provide either commit_sha or pr_ref, not both")

        link_type = "commit" if commit_sha else "pr"
        ref = commit_sha or pr_ref or ""
        link = WorkItemLink(
            link_id=new_id("link"),
            work_item_id=work_item_id,
            link_type=link_type,
            repo=repo,
            ref=ref,
        )
        self.session.add(link)
        self.session.commit()
        self.session.refresh(link)
        return link

    def link_to_dict(self, row: WorkItemLink) -> dict:
        return {
            "link_id": row.link_id,
            "work_item_id": row.work_item_id,
            "link_type": row.link_type,
            "repo": row.repo,
            "ref": row.ref,
            "created_at": _iso(row.created_at),
        }

    def list_review_queue(
        self,
        request_id: str | None = None,
        plan_revision_id: str | None = None,
    ) -> list[WorkItem]:
        query = self.session.query(WorkItem).filter(WorkItem.status == "pending_review")
        if request_id:
            query = query.filter(WorkItem.request_id == request_id)
        if plan_revision_id:
            query = query.filter(WorkItem.plan_revision_id == plan_revision_id)
        return query.order_by(WorkItem.plan_revision_id, WorkItem.depth, WorkItem.order_index).all()
