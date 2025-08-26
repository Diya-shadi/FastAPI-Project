from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models.user import UserRole

class UserRoleInfo(BaseModel):
    """Schema for dropdown options"""
    value: str
    label: str

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    role: UserRole = Field(default=UserRole.user, description="Select user role from dropdown")

class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserUpdateByAdmin(UserUpdate):
    """Admin can update more fields"""
    password: Optional[str] = Field(None, min_length=8, description="New password (optional)")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """Response for paginated user list"""
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class UserRolesResponse(BaseModel):
    """Response for dropdown options"""
    roles: List[UserRoleInfo]

class UserDetailResponse(UserResponse):
    """Detailed user information"""
    verification_token: Optional[str] = None
    reset_token: Optional[str] = None

class UserStatsResponse(BaseModel):
    """User statistics by role"""
    total_users: int
    active_users: int
    verified_users: int
    users_by_role: dict

class Token(BaseModel):
    access_token: str
    token_type: str

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

class BulkUserAction(BaseModel):
    """For bulk operations"""
    user_ids: List[int]
    action: str  # "activate", "deactivate", "delete", "verify"

class UserSearchFilter(BaseModel):
    """Search and filter parameters"""
    search: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=100)