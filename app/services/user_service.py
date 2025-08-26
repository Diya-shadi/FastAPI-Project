from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserUpdateByAdmin, UserSearchFilter
from app.utils.security import get_password_hash, generate_verification_token
import logging

logger = logging.getLogger(__name__)

class UserService:
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create verification token
        verification_token = generate_verification_token()
        
        # Create user
        db_user = User(
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role,
            verification_token=verification_token
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User created: {db_user.email} with role {db_user.role.value}")
        return db_user

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_users_with_pagination(
        db: Session, 
        filters: UserSearchFilter
    ) -> Tuple[List[User], int]:
        """Get users with pagination and filters"""
        query = db.query(User)
        
        # Apply filters
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    User.full_name.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        if filters.role:
            query = query.filter(User.role == filters.role)
            
        if filters.is_active is not None:
            query = query.filter(User.is_active == filters.is_active)
            
        if filters.is_verified is not None:
            query = query.filter(User.is_verified == filters.is_verified)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (filters.page - 1) * filters.per_page
        users = query.order_by(desc(User.created_at)).offset(offset).limit(filters.per_page).all()
        
        return users, total

    @staticmethod
    def get_users_by_role(db: Session, role: UserRole) -> List[User]:
        """Get all users by specific role"""
        return db.query(User).filter(User.role == role).all()

    @staticmethod
    def update_user(
        db: Session, 
        user_id: int, 
        user_data: UserUpdate, 
        is_admin: bool = False
    ) -> Optional[User]:
        """Update user information"""
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields that are provided
        update_data = user_data.dict(exclude_unset=True)
        
        # Check email uniqueness if email is being updated
        if "email" in update_data and update_data["email"] != db_user.email:
            existing_user = db.query(User).filter(
                and_(User.email == update_data["email"], User.id != user_id)
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken by another user"
                )
        
        # Update password if provided (only for admin updates)
        if isinstance(user_data, UserUpdateByAdmin) and user_data.password:
            update_data["hashed_password"] = get_password_hash(user_data.password)
            del update_data["password"]
        
        # Apply updates
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User updated: {db_user.email} by {'admin' if is_admin else 'user'}")
        return db_user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete user"""
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        db.delete(db_user)
        db.commit()
        
        logger.info(f"User deleted: {db_user.email}")
        return True

    @staticmethod
    def activate_user(db: Session, user_id: int) -> User:
        """Activate user account"""
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        db_user.is_active = True
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User activated: {db_user.email}")
        return db_user

    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> User:
        """Deactivate user account"""
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        db_user.is_active = False
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User deactivated: {db_user.email}")
        return db_user

    @staticmethod
    def verify_user(db: Session, user_id: int) -> User:
        """Manually verify user (admin action)"""
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        db_user.is_verified = True
        db_user.verification_token = None
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User verified: {db_user.email}")
        return db_user

    @staticmethod
    def get_user_stats(db: Session) -> dict:
        """Get user statistics"""
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        verified_users = db.query(User).filter(User.is_verified == True).count()
        
        # Users by role
        role_stats = {}
        for role in UserRole:
            count = db.query(User).filter(User.role == role).count()
            role_stats[role.value] = count
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "users_by_role": role_stats
        }

    @staticmethod
    def bulk_user_action(db: Session, user_ids: List[int], action: str) -> dict:
        """Perform bulk actions on users"""
        if not user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user IDs provided"
            )
        
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        if len(users) != len(user_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Some users not found"
            )
        
        updated_count = 0
        
        if action == "activate":
            for user in users:
                user.is_active = True
                updated_count += 1
        elif action == "deactivate":
            for user in users:
                user.is_active = False
                updated_count += 1
        elif action == "verify":
            for user in users:
                user.is_verified = True
                user.verification_token = None
                updated_count += 1
        elif action == "delete":
            for user in users:
                db.delete(user)
                updated_count += 1
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action"
            )
        
        db.commit()
        
        logger.info(f"Bulk action '{action}' performed on {updated_count} users")
        return {
            "message": f"Bulk {action} completed",
            "affected_users": updated_count
        }