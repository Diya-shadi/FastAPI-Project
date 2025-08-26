from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.user import (
    UserCreate, UserResponse, UserListResponse, UserUpdate, 
    UserUpdateByAdmin, UserDetailResponse, UserStatsResponse,
    UserSearchFilter, UserRolesResponse, UserRoleInfo
)
from app.models.user import User, UserRole
from app.services.user_service import UserService
from app.utils.deps import get_current_verified_user, get_admin_user
from app.utils.email import send_verification_email
import math

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# ==================== DASHBOARD HOME ====================
@router.get("/", response_model=dict)
async def dashboard_home(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Dashboard home with user statistics"""
    
    # Get basic stats for all users, detailed stats for admins
    basic_info = {
        "message": f"Welcome to dashboard, {current_user.full_name}!",
        "role": current_user.role.value,
        "email": current_user.email,
        "permissions": get_user_permissions(current_user.role)
    }
    
    # Add user statistics for admins and editors
    if current_user.role in [UserRole.admin, UserRole.editor]:
        stats = UserService.get_user_stats(db)
        basic_info["user_stats"] = stats
    
    return basic_info

@router.get("/profile", response_model=UserResponse)
async def get_my_dashboard_profile(current_user: User = Depends(get_current_verified_user)):
    """Get current user's profile from dashboard"""
    return current_user

@router.put("/profile", response_model=UserResponse)
async def update_my_dashboard_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile from dashboard"""
    
    # Users cannot change their own role or verification status
    if user_data.role and user_data.role != current_user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role"
        )
    
    user_data.is_verified = None
    updated_user = UserService.update_user(db, current_user.id, user_data)
    return updated_user

# ==================== USER MANAGEMENT SECTION ====================

@router.get("/users/roles", response_model=UserRolesResponse)
async def get_user_roles_dropdown(current_user: User = Depends(get_admin_user)):
    """Get available user roles for dropdown selection (Admin only)"""
    roles = [
        UserRoleInfo(
            value="admin", 
            label="Administrator", 
            description="Full system access and user management"
        ),
        UserRoleInfo(
            value="editor", 
            label="Editor", 
            description="Create and edit content, moderate users"
        ),
        UserRoleInfo(
            value="user", 
            label="User", 
            description="Basic user access and profile management"
        )
    ]
    return UserRolesResponse(roles=roles)

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_from_dashboard(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Create a new user from dashboard (Admin only)"""
    new_user = UserService.create_user(db, user_data)
    
    # Send verification email
    await send_verification_email(new_user.email, new_user.verification_token)
    
    return new_user

@router.get("/users", response_model=UserListResponse)
async def get_all_users_in_dashboard(
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get all users with pagination and filters in dashboard"""
    
    # Editors can view users, but admins see more details
    if current_user.role not in [UserRole.admin, UserRole.editor]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view users list"
        )
    
    filters = UserSearchFilter(
        search=search,
        role=role,
        is_active=is_active,
        is_verified=is_verified,
        page=page,
        per_page=per_page
    )
    
    users, total = UserService.get_users_with_pagination(db, filters)
    total_pages = math.ceil(total / per_page)
    
    return UserListResponse(
        users=users,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.get("/users/by-role/{role}")
async def list_users_by_role_in_dashboard(
    role: UserRole,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """List users by specific role in dashboard"""
    
    # Editors can view users, but admins have full access
    if current_user.role not in [UserRole.admin, UserRole.editor]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view users by role"
        )
    
    users = UserService.get_users_by_role(db, role)
    
    return {
        "role": role.value,
        "role_label": role.value.replace("_", " ").title(),
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at
            }
            for user in users
        ],
        "total_count": len(users)
    }

@router.get("/users/stats", response_model=UserStatsResponse)
async def get_user_statistics_in_dashboard(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get user statistics for dashboard (Admin only)"""
    return UserService.get_user_stats(db)

@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_by_id_in_dashboard(
    user_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get user by ID in dashboard"""
    
    # Regular users can only see their own profile
    if current_user.role == UserRole.user and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )
    
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_in_dashboard(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Update Admin User information from dashboard"""
    
    # Role-based update permissions
    if current_user.role == UserRole.user:
        # Regular users can only update their own profile
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this user"
            )
        # Regular users cannot change role or verification status
        if user_data.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to change user role"
            )
        user_data.is_verified = None
        user_data.is_active = None
    
    elif current_user.role == UserRole.editor:
        # Editors can update users but not change roles to admin
        if user_data.role == UserRole.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to assign admin role"
            )
    
    # Admin has full permissions (handled by service)
    is_admin = current_user.role == UserRole.admin
    updated_user = UserService.update_user(db, user_id, user_data, is_admin)
    
    return updated_user

@router.put("/users/{user_id}/admin", response_model=UserResponse)
async def update_user_by_admin_in_dashboard(
    user_id: int,
    user_data: UserUpdateByAdmin,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update user information with admin privileges from dashboard (Admin only)"""
    updated_user = UserService.update_user(db, user_id, user_data, is_admin=True)
    return updated_user

@router.delete("/users/{user_id}")
async def delete_user_in_dashboard(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete user from dashboard (Admin only)"""
    
    # Prevent admin from deleting themselves
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    UserService.delete_user(db, user_id)
    return {"message": "User deleted successfully"}

@router.patch("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user_in_dashboard(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Activate user account from dashboard (Admin only)"""
    return UserService.activate_user(db, user_id)

@router.patch("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user_in_dashboard(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Deactivate user account from dashboard (Admin only)"""
    
    # Prevent admin from deactivating themselves
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    return UserService.deactivate_user(db, user_id)

@router.patch("/users/{user_id}/verify", response_model=UserResponse)
async def verify_user_manually_in_dashboard(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Manually verify user account from dashboard (Admin only)"""
    return UserService.verify_user(db, user_id)


# ==================== DASHBOARD ANALYTICS & REPORTS ====================

@router.get("/analytics/user-growth")
async def get_user_growth_analytics(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get user growth analytics for dashboard (Admin only)"""
    
    # Get users registered in the last 30 days
    from datetime import datetime, timedelta
    from sqlalchemy import func, extract
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Users registered in last 30 days
    recent_users = db.query(User).filter(
        User.created_at >= thirty_days_ago
    ).count()
    
    # Users by month (last 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_stats = db.query(
        extract('year', User.created_at).label('year'),
        extract('month', User.created_at).label('month'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= six_months_ago
    ).group_by(
        extract('year', User.created_at),
        extract('month', User.created_at)
    ).order_by(
        extract('year', User.created_at),
        extract('month', User.created_at)
    ).all()
    
    return {
        "recent_users_30_days": recent_users,
        "monthly_growth": [
            {
                "year": int(stat.year),
                "month": int(stat.month),
                "users_registered": stat.count
            }
            for stat in monthly_stats
        ],
        "total_users": db.query(User).count()
    }

@router.get("/reports/user-activity")
async def get_user_activity_report(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get user activity report for dashboard (Admin only)"""
    
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()
    unverified_users = db.query(User).filter(User.is_verified == False).count()
    
    # Role distribution
    role_distribution = {}
    for role in UserRole:
        count = db.query(User).filter(User.role == role).count()
        role_distribution[role.value] = count
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "verified_users": verified_users,
        "unverified_users": unverified_users,
        "role_distribution": role_distribution,
        "activation_rate": round((active_users / total_users * 100), 2) if total_users > 0 else 0,
        "verification_rate": round((verified_users / total_users * 100), 2) if total_users > 0 else 0
    }

# ==================== HELPER FUNCTIONS ====================

def get_user_permissions(role: UserRole) -> List[str]:
    """Helper function to return permissions based on role"""
    permissions = {
        UserRole.admin: [
            "read_users", "create_users", "update_users", "delete_users", 
            "manage_system", "access_admin_panel", "view_analytics", 
            "bulk_operations", "manage_roles"
        ],
        UserRole.editor: [
            "read_users", "update_limited_users", "create_content", 
            "edit_content", "delete_own_content", "moderate_content",
            "view_user_stats"
        ],
        UserRole.user: [
            "read_own_profile", "update_own_profile", "view_content",
            "change_password"
        ]
    }
    return permissions.get(role, [])