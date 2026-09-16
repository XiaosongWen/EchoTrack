from datetime import date
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.commitment import Commitment
from models.record import Record
from schemas.record import RecordCreate, RecordUpdate, HeatmapEntry


class RecordService:
    @staticmethod
    async def _validate_create_record(db: AsyncSession, data: RecordCreate) -> None:
        """Validate record creation — verify commitment exists and prevent habit duplicates."""
        if data.commitment_id:
            # Verify commitment exists
            result = await db.execute(
                select(Commitment).where(Commitment.id == data.commitment_id)
            )
            commitment = result.scalar_one_or_none()
            if commitment is None:
                raise ValueError(f"Commitment {data.commitment_id} not found")

            # For habit-type commitments, prevent duplicate records on the same date
            if commitment.type == 'habit':
                existing = await db.execute(
                    select(Record).where(
                        Record.commitment_id == data.commitment_id,
                        Record.date == data.date,
                    )
                )
                if existing.scalar_one_or_none() is not None:
                    raise ValueError(
                        f"Record already exists for commitment {data.commitment_id} on {data.date}"
                    )

    @staticmethod
    async def get_records(
        db: AsyncSession, 
        commitment_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: str | None = None
    ) -> list[Record]:
        query = select(Record)
        if commitment_id:
            query = query.where(Record.commitment_id == commitment_id)
        if date_from:
            query = query.where(Record.date >= date_from)
        if date_to:
            query = query.where(Record.date <= date_to)
        if status:
            query = query.where(Record.status == status)
            
        query = query.order_by(Record.date.desc(), Record.sort_order.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_record(db: AsyncSession, record_id: UUID) -> Record | None:
        result = await db.execute(select(Record).where(Record.id == record_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_record(db: AsyncSession, data: RecordCreate) -> Record:
        await RecordService._validate_create_record(db, data)
        record = Record(**data.model_dump())
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def batch_create_records(db: AsyncSession, data_list: list[RecordCreate]) -> list[Record]:
        # Validate all records first to avoid partial commits
        for data in data_list:
            await RecordService._validate_create_record(db, data)

        records = [Record(**data.model_dump()) for data in data_list]
        db.add_all(records)
        await db.commit()
        for r in records:
            await db.refresh(r)
        return records

    @staticmethod
    async def update_record(db: AsyncSession, record_id: UUID, data: RecordUpdate) -> Record | None:
        record = await RecordService.get_record(db, record_id)
        if record is None:
            return None
            
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(record, field, value)
            
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def delete_record(db: AsyncSession, record_id: UUID) -> bool:
        record = await RecordService.get_record(db, record_id)
        if record is None:
            return False
        await db.delete(record)
        await db.commit()
        return True

    @staticmethod
    async def reorder_records(
        db: AsyncSession, items: list[tuple[UUID, int]],
    ) -> None:
        """Batch-update sort_order for a list of records."""
        for record_id, sort_order in items:
            result = await db.execute(
                select(Record).where(Record.id == record_id)
            )
            record = result.scalar_one_or_none()
            if record:
                record.sort_order = sort_order
        await db.commit()

    @staticmethod
    async def get_heatmap(
        db: AsyncSession, user_id: UUID, date_from: date, date_to: date,
    ) -> list[HeatmapEntry]:
        """Count done records per day for the user's commitments."""
        rows = await db.execute(
            select(Record.date, func.count(Record.id))
            .join(Commitment, Record.commitment_id == Commitment.id)
            .where(
                Commitment.user_id == user_id,
                Record.date >= date_from,
                Record.date <= date_to,
                Record.status == 'done',
            )
            .group_by(Record.date)
            .order_by(Record.date)
        )
        return [HeatmapEntry(date=row[0], count=row[1]) for row in rows.all()]
