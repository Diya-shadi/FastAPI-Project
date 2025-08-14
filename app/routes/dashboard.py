from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.user import UserResponse
from app.models.user import User, UserRole
from app.utils.deps import get_current_verified_user, get_admin_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/", response_model=dict)
async def dashboard_home(current_user: User = Depends(get_current_verified_user)):
    return {
        "message": f"Welcome to dashboard, {current_user.full_name}!",
        "role": current_user.role.value,
        "email": current_user.email
    }

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return users

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_verified_user)):
    return current_user

@router.get("/admin-only")
async def admin_only_route(current_user: User = Depends(get_admin_user)):
    return {"message": "This is an admin-only route", "admin": current_user.full_name}