from fastapi import APIRouter, Depends, Request

from core.auth import get_current_user
from models.user import User
from schemas.user import UserRead
from schemas.response import SingleResponse

router = APIRouter(tags=["users"])


@router.get("/api/v1/users/me", response_model=SingleResponse[UserRead])
async def get_my_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    request_id = getattr(request.state, "request_id", "UNKNOWN")
    return SingleResponse(request_id=request_id, data=current_user)
