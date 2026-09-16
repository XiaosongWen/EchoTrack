from uuid import UUID
from sqlalchemy import select, exc
from sqlalchemy.ext.asyncio import AsyncSession
from models.label import Label, EntityLabel
from schemas.label import LabelCreate, LabelUpdate, EntityLabelAttach

DEFAULT_SEED_LABELS = [
    {"name": "Health", "color": "#10b981"},
    {"name": "Morning", "color": "#f59e0b"},
    {"name": "Mindfulness", "color": "#8b5cf6"},
    {"name": "Learning", "color": "#3b82f6"},
    {"name": "Career", "color": "#ec4899"},
    {"name": "Focus", "color": "#6366f1"},
]

class LabelService:
    @staticmethod
    async def list_labels(db: AsyncSession, user_id: UUID) -> list[Label]:
        query = select(Label).where(Label.user_id == user_id).order_by(Label.name.asc())
        result = await db.execute(query)
        labels = list(result.scalars().all())
        if not labels:
            for seed in DEFAULT_SEED_LABELS:
                db.add(Label(user_id=user_id, **seed))
            try:
                await db.commit()
            except Exception:
                await db.rollback()
            result = await db.execute(query)
            labels = list(result.scalars().all())
        return labels

    @staticmethod
    async def get_label(db: AsyncSession, label_id: UUID, user_id: UUID) -> Label | None:
        result = await db.execute(
            select(Label).where(Label.id == label_id, Label.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_label(db: AsyncSession, user_id: UUID, data: LabelCreate) -> Label:
        label = Label(
            user_id=user_id,
            **data.model_dump()
        )
        db.add(label)
        try:
            await db.commit()
            await db.refresh(label)
        except exc.IntegrityError:
            await db.rollback()
            raise ValueError(f"Label with name '{data.name}' already exists.")
        return label

    @staticmethod
    async def update_label(db: AsyncSession, label_id: UUID, user_id: UUID, data: LabelUpdate) -> Label | None:
        label = await LabelService.get_label(db, label_id, user_id)
        if not label:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(label, field, value)
            
        try:
            await db.commit()
            await db.refresh(label)
        except exc.IntegrityError:
            await db.rollback()
            raise ValueError(f"Label with name '{data.name}' already exists.")
        return label

    @staticmethod
    async def delete_label(db: AsyncSession, label_id: UUID, user_id: UUID) -> bool:
        label = await LabelService.get_label(db, label_id, user_id)
        if not label:
            return False
        await db.delete(label)
        await db.commit()
        return True
        
    @staticmethod
    async def attach_label(db: AsyncSession, label_id: UUID, user_id: UUID, data: EntityLabelAttach) -> bool:
        label = await LabelService.get_label(db, label_id, user_id)
        if not label:
            return False
            
        # Check if already attached — idempotent
        existing = await db.execute(
            select(EntityLabel).where(
                EntityLabel.label_id == label_id,
                EntityLabel.entity_type == data.entity_type,
                EntityLabel.entity_id == data.entity_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            return True  # already attached, nothing to do

        entity_label = EntityLabel(
            label_id=label_id,
            entity_type=data.entity_type,
            entity_id=data.entity_id
        )
        db.add(entity_label)
        await db.commit()
        return True
        
    @staticmethod
    async def detach_label(db: AsyncSession, label_id: UUID, user_id: UUID, data: EntityLabelAttach) -> bool:
        label = await LabelService.get_label(db, label_id, user_id)
        if not label:
            return False
            
        result = await db.execute(
            select(EntityLabel).where(
                EntityLabel.label_id == label_id,
                EntityLabel.entity_type == data.entity_type,
                EntityLabel.entity_id == data.entity_id
            )
        )
        entity_label = result.scalar_one_or_none()
        if entity_label:
            await db.delete(entity_label)
            try:
                await db.commit()
            except Exception:
                await db.rollback()
                raise
        return True
