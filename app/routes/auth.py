from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
# from app.schemas.user import UserCreate, UserLogin, Token, UserResponse, PasswordReset, PasswordResetConfirm, PasswordChange
from app.schemas.user import (
    UserCreate, UserLogin, Token, UserResponse, PasswordReset, 
    PasswordResetConfirm, PasswordChange, UserRoleInfo, UserRolesResponse
)
from app.models.user import User, UserRole
from app.utils.security import (
    verify_password, get_password_hash, create_access_token,
    generate_verification_token, generate_reset_token
)
from app.utils.email import send_verification_email, send_password_reset_email
from app.utils.deps import get_current_user, get_current_verified_user
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/user-roles", response_model=UserRolesResponse)
async def get_user_roles():
    """Get available user roles for dropdown"""
    roles = [
        UserRoleInfo(value="admin", label="Administrator"),
        UserRoleInfo(value="user", label="User"),
        UserRoleInfo(value="editor", label="Editor")
    ]
    return UserRolesResponse(roles=roles)

@router.post("/register/{role}", response_model=dict)
async def register(
    role: UserRole,  
    user: UserCreate, 
    db: Session = Depends(get_db)
):
    # Check if email exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create verification token
    verification_token = generate_verification_token()

    # Create user
    db_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        role=role,  # 👈 comes from path dropdown
        verification_token=verification_token
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Send verification email
    await send_verification_email(user.email, verification_token)

    return {
        "message": "User registered successfully. Please check your email to verify your account.",
        "user_role": role.value
    }

@router.get("/verify-email")
async def verify_email(token: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    user.is_active = True
    user.is_verified = True
    user.verification_token = None
    
    db.commit()
    
    return {"message": "Email verified successfully"}

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not activated. Please verify your email."
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
async def forgot_password(password_reset: PasswordReset, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == password_reset.email).first()
    
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a password reset link has been sent."}
    
    reset_token = generate_reset_token()
    user.reset_token = reset_token
    db.commit()
    
    await send_password_reset_email(password_reset.email, reset_token)
    
    return {"message": "If the email exists, a password reset link has been sent."}

@router.post("/reset-password")
async def reset_password(reset_data: PasswordResetConfirm, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == reset_data.token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.reset_token = None
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user