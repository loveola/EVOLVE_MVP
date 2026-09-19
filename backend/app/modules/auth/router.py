from fastapi import APIRouter, Depends
from app.modules.auth.schemas import UserResponse
from app.modules.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user


@router.get("/admin/status")
async def get_admin_status(current_user: UserResponse = Depends(get_current_user)):
    return {"is_admin": bool(current_user.is_admin)}

