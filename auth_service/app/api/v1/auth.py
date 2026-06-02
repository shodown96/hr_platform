from app.core.db import SessionDep
from app.core.dependencies.auth import get_current_user
from app.core.shared.cache.permissions import (
    PermissionCache,
    PermissionsDep,
    get_permission_cache,
)
from app.messaging.rabbitmq import RabbitMQDep
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
from app.services.email import EmailService
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.services.roles import RoleService

router = APIRouter()


@router.post(
    "/sign-up", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def sign_up(
    user_data: UserCreate,
    db: SessionDep,
    rabbitmq: RabbitMQDep,
    cache: PermissionCache = Depends(get_permission_cache),
    # dependencies=Depends(anonymous_only),
):
    """Sign up as a new user"""

    user = await AuthService.create_user(db, rabbitmq, user_data)

    await RoleService.assign_default_role_to_new_user(db, rabbitmq, cache, user.id)

    permissions = await AuthService.get_user_permissions(db, cache, user.id)

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
async def sign_in(
    db: SessionDep,
    cache: PermissionsDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
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
    permissions = await AuthService.get_user_permissions(db, cache, str(user.id))

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

    email_service = EmailService()
    await email_service.send_otp_email(token.email, token.otp_code)

    return {"message": "OTP sent to email"}


@router.post("/reset-password")
async def reset_password(
    db: SessionDep,
    rabbitmq: RabbitMQDep,
    reset_data: VerifyResetRequest,
):
    """Verify OTP and reset password (single step)"""

    await AuthService.verify_and_reset(
        db, rabbitmq, reset_data.email, reset_data.otp_code, reset_data.new_password
    )

    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    db: SessionDep,
    rabbitmq: RabbitMQDep,
    change_data: ChangePasswordRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """Change password (authenticated)"""

    await AuthService.change_password(
        db,
        rabbitmq,
        current_user.user_id,
        change_data.current_password,
        change_data.new_password,
    )
    # TODO: Send email regarding change of password

    return {"message": "Password changed successfully"}
