from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from database import get_db
from models.user import User
from schemas.label import LabelCreate, LabelUpdate, LabelResponse, EntityLabelAttach
from schemas.response import SingleResponse, ListResponse, Pagination
from services.label_service import LabelService

router = APIRouter(prefix="/api/v1/labels", tags=["labels"])


@router.get("", response_model=ListResponse[LabelResponse])
async def list_labels(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    labels = await LabelService.list_labels(db, current_user.id)
    request_id = getattr(request.state, "request_id", "UNKNOWN")
    pagination = Pagination(page=1, page_size=len(labels), total_rows=len(labels))
    return ListResponse(request_id=request_id, data=labels, pagination=pagination)


@router.post("", response_model=SingleResponse[LabelResponse], status_code=status.HTTP_201_CREATED)
async def create_label(
    request: Request,
    data: LabelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        label = await LabelService.create_label(db, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    request_id = getattr(request.state, "request_id", "UNKNOWN")
    return SingleResponse(request_id=request_id, data=label)


@router.get("/{label_id}", response_model=SingleResponse[LabelResponse])
async def get_label(
    request: Request,
    label_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    label = await LabelService.get_label(db, label_id, current_user.id)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    request_id = getattr(request.state, "request_id", "UNKNOWN")
    return SingleResponse(request_id=request_id, data=label)


@router.put("/{label_id}", response_model=SingleResponse[LabelResponse])
async def update_label(
    request: Request,
    label_id: UUID,
    data: LabelUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        label = await LabelService.update_label(db, label_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    request_id = getattr(request.state, "request_id", "UNKNOWN")
    return SingleResponse(request_id=request_id, data=label)


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    label_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await LabelService.delete_label(db, label_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Label not found")


@router.post("/{label_id}/attach", status_code=status.HTTP_204_NO_CONTENT)
async def attach_label(
    label_id: UUID,
    data: EntityLabelAttach,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await LabelService.attach_label(db, label_id, current_user.id, data)
    if not ok:
        raise HTTPException(status_code=404, detail="Label not found")


@router.post("/{label_id}/detach", status_code=status.HTTP_204_NO_CONTENT)
async def detach_label(
    label_id: UUID,
    data: EntityLabelAttach,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await LabelService.detach_label(db, label_id, current_user.id, data)
    if not ok:
        raise HTTPException(status_code=404, detail="Label not found")
