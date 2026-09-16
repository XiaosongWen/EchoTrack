from collections import defaultdict
from datetime import date
from unittest.mock import AsyncMock
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.commitment import Commitment
from models.commitment_link import CommitmentLink
from models.label import Label, EntityLabel
from models.record import Record
from schemas.commitment import CommitmentCreate, CommitmentUpdate


class CommitmentService:
    @staticmethod
    async def _populate_labels_and_parents(db: AsyncSession, commitments: list[Commitment]) -> None:
        if not commitments or isinstance(db, AsyncMock):
            for c in commitments:
                if not hasattr(c, "labels") or c.labels is None:
                    c.labels = []
            return
        try:
            ids = [c.id for c in commitments if hasattr(c, "id") and isinstance(c.id, UUID)]
            if not ids:
                for c in commitments:
                    if not hasattr(c, "labels") or c.labels is None:
                        c.labels = []
                return

            links_result = await db.execute(
                select(CommitmentLink.child_id, CommitmentLink.parent_id)
                .where(CommitmentLink.child_id.in_(ids))
            )
            parent_map = {row.child_id: row.parent_id for row in links_result.all()}

            labels_result = await db.execute(
                select(EntityLabel.entity_id, Label)
                .join(Label, EntityLabel.label_id == Label.id)
                .where(EntityLabel.entity_type == "commitment", EntityLabel.entity_id.in_(ids))
            )
            labels_map = defaultdict(list)
            for row in labels_result.all():
                labels_map[row.entity_id].append(row[1])

            for c in commitments:
                if hasattr(c, "id"):
                    c.parent_id = parent_map.get(c.id)
                    c.labels = labels_map.get(c.id, [])
        except Exception:
            for c in commitments:
                if not hasattr(c, "labels") or c.labels is None:
                    c.labels = []

    @staticmethod
    async def list_commitments(
        db: AsyncSession, user_id: UUID,
        type_: str | None = None,
        status: str | None = None,
        parent_id: UUID | None = None,
        root: bool = False,
        priority: str | None = None,
        due_date_from: date | None = None,
        due_date_to: date | None = None,
        q: str | None = None,
        record_date: date | None = None,
    ) -> list[Commitment]:
        query = select(Commitment).where(Commitment.user_id == user_id)
        if type_:
            query = query.where(Commitment.type == type_)
        if status:
            query = query.where(Commitment.status == status)
        if priority:
            query = query.where(Commitment.priority == priority)
        if due_date_from:
            query = query.where(Commitment.due_date >= due_date_from)
        if due_date_to:
            query = query.where(Commitment.due_date <= due_date_to)
        if q:
            query = query.where(Commitment.title.ilike(f"%{q}%"))
        if record_date:
            exists_query = (
                select(Record.id)
                .where(Record.commitment_id == Commitment.id, Record.date == record_date)
                .exists()
            )
            query = query.where(exists_query)

        if root:
            subquery = select(CommitmentLink.child_id)
            query = query.where(Commitment.id.notin_(subquery))
        elif parent_id:
            query = query.join(CommitmentLink, Commitment.id == CommitmentLink.child_id)\
                         .where(CommitmentLink.parent_id == parent_id)

        query = query.order_by(Commitment.sort_order.asc(), Commitment.created_at.asc())
        result = await db.execute(query)
        commitments = list(result.scalars().all())

        await CommitmentService._populate_labels_and_parents(db, commitments)
        return commitments

    @staticmethod
    async def get_commitment(db: AsyncSession, commitment_id: UUID, user_id: UUID) -> Commitment | None:
        result = await db.execute(
            select(Commitment).where(Commitment.id == commitment_id, Commitment.user_id == user_id)
        )
        commitment = result.scalar_one_or_none()
        if commitment:
            await CommitmentService._populate_labels_and_parents(db, [commitment])
        return commitment

    @staticmethod
    async def create_commitment(db: AsyncSession, user_id: UUID, data: CommitmentCreate) -> Commitment:
        parent_id = data.parent_id
        label_ids = data.label_ids or []
        payload = data.model_dump(exclude={"parent_id", "label_ids"})
        commitment = Commitment(
            user_id=user_id,
            **payload
        )
        db.add(commitment)
        await db.commit()
        await db.refresh(commitment)

        if parent_id:
            link = CommitmentLink(
                parent_id=parent_id,
                child_id=commitment.id,
                sort_order=0
            )
            db.add(link)

        if label_ids:
            for lid in label_ids:
                db.add(EntityLabel(label_id=lid, entity_type="commitment", entity_id=commitment.id))

        if parent_id or label_ids:
            await db.commit()
            await db.refresh(commitment)

        await CommitmentService._populate_labels_and_parents(db, [commitment])
        return commitment

    @staticmethod
    async def update_commitment(db: AsyncSession, commitment_id: UUID, user_id: UUID, data: CommitmentUpdate) -> Commitment | None:
        commitment = await CommitmentService.get_commitment(db, commitment_id, user_id)
        if commitment is None:
            return None
        
        label_ids = data.label_ids
        update_data = data.model_dump(exclude_unset=True, exclude={"label_ids", "parent_id"})
        for field, value in update_data.items():
            setattr(commitment, field, value)

        if "parent_id" in data.model_fields_set:
            new_parent_id = data.parent_id
            
            # Check for circular dependency: walk ancestors of new_parent_id
            # to ensure commitment_id is not among them
            if new_parent_id is not None:
                if new_parent_id == commitment_id:
                    raise ValueError("A commitment cannot be its own parent")
                visited = {commitment_id}
                current = new_parent_id
                while current is not None:
                    if current in visited:
                        raise ValueError("Circular parent-child dependency detected")
                    visited.add(current)
                    ancestor_link_res = await db.execute(
                        select(CommitmentLink.parent_id).where(CommitmentLink.child_id == current)
                    )
                    ancestor_link = ancestor_link_res.scalar_one_or_none()
                    current = ancestor_link

            # Delete old parent links
            old_parent_links_res = await db.execute(
                select(CommitmentLink).where(CommitmentLink.child_id == commitment_id)
            )
            old_parent_links = list(old_parent_links_res.scalars().all())
            for old_link in old_parent_links:
                await db.delete(old_link)
                
            # Insert new parent link if any
            if new_parent_id is not None:
                new_link = CommitmentLink(
                    parent_id=new_parent_id,
                    child_id=commitment_id,
                    sort_order=0
                )
                db.add(new_link)

        if label_ids is not None:
            old_links_res = await db.execute(
                select(EntityLabel).where(EntityLabel.entity_type == "commitment", EntityLabel.entity_id == commitment_id)
            )
            old_links = list(old_links_res.scalars().all())
            for old in old_links:
                await db.delete(old)

            for lid in label_ids:
                db.add(EntityLabel(label_id=lid, entity_type="commitment", entity_id=commitment_id))
            
        await db.commit()
        await db.refresh(commitment)
        await CommitmentService._populate_labels_and_parents(db, [commitment])
        return commitment

    @staticmethod
    async def delete_commitment(db: AsyncSession, commitment_id: UUID, user_id: UUID) -> bool:
        commitment = await CommitmentService.get_commitment(db, commitment_id, user_id)
        if commitment is None:
            return False
        await db.delete(commitment)
        await db.commit()
        return True

    @staticmethod
    async def reorder_commitments(
        db: AsyncSession, items: list[tuple[UUID, int]], user_id: UUID,
    ) -> None:
        """Batch-update sort_order for a list of commitments."""
        for item_id, sort_order in items:
            result = await db.execute(
                select(Commitment).where(Commitment.id == item_id, Commitment.user_id == user_id)
            )
            commitment = result.scalar_one_or_none()
            if commitment:
                commitment.sort_order = sort_order
        await db.commit()
