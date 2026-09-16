from collections import defaultdict
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from database import get_db
from models.user import User
from schemas.commitment import CommitmentCreate, CommitmentUpdate, CommitmentRead
from schemas.record import RecordCreate, RecordUpdate, RecordRead, RecordBatchCreate, HeatmapEntry
from schemas.daily import DailyResponse, DailyHabitCheckin
from schemas.response import SingleResponse, ListResponse, Pagination, ReorderItem
from services.commitment_service import CommitmentService
from services.record_service import RecordService
from services.progress_service import ProgressService

router = APIRouter(tags=["pursuits"])


@router.get("/api/v1/pursuits/commitments", response_model=ListResponse[CommitmentRead])
async def list_commitments(
    request: Request,
    type: str | None = Query(None),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    parent_id: UUID | None = Query(None),
    root: bool = Query(False),
    date: date | None = Query(None),
    due_date_from: date | None = Query(None),
    due_date_to: date | None = Query(None),
    q: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    commitments = await CommitmentService.list_commitments(
        db,
        current_user.id,
        type_=type,
        status=status,
        priority=priority,
        parent_id=parent_id,
        root=root,
        record_date=date,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        q=q,
    )
    # Batch-calculate progress (1-2 queries instead of N)
    if commitments:
        progress_map = await ProgressService.compute_progress_batch(db, commitments)
        for c in commitments:
            c.progress = progress_map.get(c.id)

    request_id = getattr(request.state, "request_id", "UNKNOWN")
    pagination = Pagination(page=1, page_size=len(commitments), total_rows=len(commitments))
    return ListResponse(request_id=request_id, data=commitments, pagination=pagination)


@router.post("/api/v1/pursuits/commitments", response_model=SingleResponse[CommitmentRead], status_code=status.HTTP_201_CREATED)
async def create_commitment(
    request: Request,
    data: CommitmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    commitment = await CommitmentService.create_commitment(db, current_user.id, data)
    commitment.progress = await ProgressService.compute_progress(db, commitment)
    request_id = getattr(request.state, "request_id", "UNKNOWN")
    return SingleResponse(request_id=request_id, data=commitment)


@router.put("/api/v1/pursuits/commitments/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_commitments(
    data: list[ReorderItem],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = [(item.id, item.sort_order) for item in data]
    await CommitmentService.reorder_commitments(db, items, current_user.id)


@router.get("/api/v1/pursuits/commitments/{commitment_id}", response_model=SingleResponse[CommitmentRead])
async def get_commitment(
    request: Request,
    commitment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    commitment = await CommitmentService.get_commitment(db, commitment_id, current_user.id)
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    commitment.progress = await ProgressService.compute_progress(db, commitment)
    request_id = getattr(request.state, "request_id", "UNKNOWN")
    return SingleResponse(request_id=request_id, data=commitment)


@router.put("/api/v1/pursuits/commitments/{commitment_id}", response_model=SingleResponse[CommitmentRead])
async def update_commitment(
    request: Request,
    commitment_id: UUID,
    data: CommitmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    commitment = await CommitmentService.update_commitment(db, commitment_id, current_user.id, data)
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    commitment.progress = await ProgressService.compute_progress(db, commitment)
    request_id = getattr(request.state, "request_id", "UNKNOWN")
    return SingleResponse(request_id=request_id, data=commitment)


@router.delete("/api/v1/pursuits/commitments/{commitment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_commitment(
    commitment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await CommitmentService.delete_commitment(db, commitment_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Commitment not found")


@router.get("/api/v1/pursuits/records", response_model=ListResponse[RecordRead])
async def list_records(
    request: Request,
    commitment_id: UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    records = await RecordService.get_records(db, commitment_id=commitment_id, date_from=date_from, date_to=date_to, status=status)
    request_id = getattr(request.state, "request_id", "UNKNOWN")
    pagination = Pagination(page=1, page_size=len(records), total_rows=len(records))
    return ListResponse(request_id=request_id, data=records, pagination=pagination)


@router.post("/api/v1/pursuits/records", response_model=SingleResponse[RecordRead], status_code=status.HTTP_201_CREATED)
async def create_record(
    request: Request,
    data: RecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        record = await RecordService.create_record(db, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    request_id = getattr(request.state, "request_id", "UNKNOWN")
    return SingleResponse(request_id=request_id, data=record)


@router.post("/api/v1/pursuits/records/batch", response_model=ListResponse[RecordRead], status_code=status.HTTP_201_CREATED)
async def batch_create_records(
    request: Request,
    data: RecordBatchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        records = await RecordService.batch_create_records(db, data.records)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    request_id = getattr(request.state, "request_id", "UNKNOWN")
    pagination = Pagination(page=1, page_size=len(records), total_rows=len(records))
    return ListResponse(request_id=request_id, data=records, pagination=pagination)


@router.put("/api/v1/pursuits/records/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_records(
    data: list[ReorderItem],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = [(item.id, item.sort_order) for item in data]
    await RecordService.reorder_records(db, items)


@router.get("/api/v1/pursuits/records/{record_id}", response_model=SingleResponse[RecordRead])
async def get_record(
    request: Request,
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await RecordService.get_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    request_id = getattr(request.state, "request_id", "UNKNOWN")
    return SingleResponse(request_id=request_id, data=record)


@router.put("/api/v1/pursuits/records/{record_id}", response_model=SingleResponse[RecordRead])
async def update_record(
    request: Request,
    record_id: UUID,
    data: RecordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await RecordService.update_record(db, record_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    request_id = getattr(request.state, "request_id", "UNKNOWN")
    return SingleResponse(request_id=request_id, data=record)


@router.delete("/api/v1/pursuits/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await RecordService.delete_record(db, record_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Record not found")


@router.get("/api/v1/pursuits/heatmap", response_model=ListResponse[HeatmapEntry])
async def get_heatmap(
    request: Request,
    date_from: date = Query(alias="from"),
    date_to: date = Query(alias="to"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entries = await RecordService.get_heatmap(db, current_user.id, date_from, date_to)
    request_id = getattr(request.state, "request_id", "UNKNOWN")
    pagination = Pagination(page=1, page_size=len(entries), total_rows=len(entries))
    return ListResponse(request_id=request_id, data=entries, pagination=pagination)


@router.get("/api/v1/pursuits/daily/{target_date}", response_model=SingleResponse[DailyResponse])
async def get_daily(
    request: Request,
    target_date: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Active habits
    habits = await CommitmentService.list_commitments(db, current_user.id, type_="habit", status="active")

    # 2. Batch compute progress for all habits (1-2 queries vs N)
    if habits:
        habit_progress = await ProgressService.compute_progress_batch(db, habits)
    else:
        habit_progress = {}

    for h in habits:
        h.progress = habit_progress.get(h.id)

    # 3. Single query for ALL today's records (replaces N per-habit queries + free-records query)
    all_today_records = await RecordService.get_records(db, date_from=target_date, date_to=target_date)

    # Group records by commitment_id (None = free-form)
    records_by_commitment: dict[UUID | None, list] = defaultdict(list)
    for r in all_today_records:
        records_by_commitment[r.commitment_id].append(r)

    daily_habits = []
    for h in habits:
        recs = records_by_commitment.get(h.id)
        daily_habits.append(
            DailyHabitCheckin(
                commitment=h,
                today_record=recs[0] if recs else None,
            )
        )

    # 4. Today's tasks
    tasks = await CommitmentService.list_commitments(db, current_user.id, type_="task")
    daily_tasks = [t for t in tasks if t.due_date == target_date]
    if daily_tasks:
        task_progress = await ProgressService.compute_progress_batch(db, daily_tasks)
        for t in daily_tasks:
            t.progress = task_progress.get(t.id)

    # 5. Free records (without commitment_id) — already loaded in step 3
    free_records = records_by_commitment.get(None, [])

    response_data = DailyResponse(
        date=target_date,
        habits=daily_habits,
        tasks=daily_tasks,
        free_records=free_records,
    )
    request_id = getattr(request.state, "request_id", "UNKNOWN")
    return SingleResponse(request_id=request_id, data=response_data)
