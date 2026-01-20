from app.core.db import SessionDep
from app.core.dependencies.auth import get_current_user
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    TokenData,
    TokenResponse,
    UserCreate,
    UserResponse,
    VerifyResetRequest,
)
from app.services.auth import AuthService
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()


@router.post(
    "/sign-up", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def sign_up(
    user_data: UserCreate,
    db: SessionDep,
    # dependencies=Depends(anonymous_only),
):
    """Sign up as a new user"""

    user = await AuthService.create_user(db, user_data)

    # TODO: Add basic permissions to the user

    # Get user permissions
    permissions = await AuthService.get_user_permissions(db, str(user.id))

    # Create access token
    access_token = AuthService.create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "is_superuser": user.is_superuser,
            "permissions": permissions,
        }
    )
    return TokenResponse(
        access_token=access_token, user=UserResponse.model_validate(user)
    )


@router.post("/sign-in", response_model=TokenResponse)
async def sign_in(db: SessionDep, form_data: OAuth2PasswordRequestForm = Depends()):
    """Sign in and get access token"""
    user = await AuthService.authenticate_user(
        db, form_data.username, form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user permissions
    permissions = await AuthService.get_user_permissions(db, str(user.id))

    # Create access token
    access_token = AuthService.create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "is_superuser": user.is_superuser,
            "permissions": permissions,
        }
    )
    return TokenResponse(
        access_token=access_token, user=UserResponse.model_validate(user)
    )


@router.post("/forgot-password")
async def forgot_password(
    db: SessionDep,
    request_data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
):
    """Send OTP to email"""

    token = await AuthService.request_reset(db, request_data.email)

    # Send email in background
    # TODO: Email service
    # email_service = EmailService()

    # background_tasks.add_task(
    #     email_service.send_otp_email,
    #     to_email=token.email,
    #     otp_code=token.otp_code
    # )

    return {"message": "OTP sent to email"}


@router.post("/reset-password")
async def reset_password(
    db: SessionDep,
    reset_data: VerifyResetRequest,
):
    """Verify OTP and reset password (single step)"""

    await AuthService.verify_and_reset(
        db, reset_data.email, reset_data.otp_code, reset_data.new_password
    )

    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    db: SessionDep,
    change_data: ChangePasswordRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """Change password (authenticated)"""

    await AuthService.change_password(
        db, current_user.user_id, change_data.current_password, change_data.new_password
    )

    return {"message": "Password changed successfully"}
