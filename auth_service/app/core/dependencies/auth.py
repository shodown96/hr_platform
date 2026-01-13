from typing import Annotated

from app.core.config import settings
from app.core.db import SessionDep
from app.core.logger import logging
from app.models.auth import User
from app.schemas.auth import TokenData
from app.services.auth import AuthService, TokenType, oauth2_scheme
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def get_current_user(
    db: SessionDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Validate JWT token and return current user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        token_data = TokenData(
            user_id=user_id,
            is_superuser=payload.get("is_superuser", False),
            permissions=payload.get("permissions", []),
        )
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user: User | None = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure user is active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Ensure user is superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


async def get_optional_user(request: Request, db: SessionDep) -> dict | None:
    token = request.headers.get("Authorization")
    if not token:
        return None

    try:
        token_type, _, token_value = token.partition(" ")
        if token_type.lower() != "bearer" or not token_value:
            return None

        token_data = await AuthService.verify_token(token_value, TokenType.ACCESS, db)
        if token_data is None:
            return None

        return await get_current_user(token_value, db=db)

    except HTTPException as http_exc:
        if http_exc.status_code != 401:
            logger.error(
                f"Unexpected HTTPException in get_optional_user: {http_exc.detail}"
            )
        return None

    except Exception as exc:
        logger.error(f"Unexpected error in get_optional_user: {exc}")
        return None


async def anonymous_only(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
):
    """
    Allows only unauthenticated users.
    If a valid token is provided, reject the request.
    """
    if not token:
        return

    try:
        jwt.decode(token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.ALGORITHM])
    except JWTError:
        # invalid token → treat as anonymous
        return

    # valid token = authenticated user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Authenticated users cannot access this endpoint",
    )


def check_permission(required_permission: str):
    """Decorator to check if user has specific permission"""

    async def permission_checker(
        current_user: User = Depends(get_current_user), db=SessionDep
    ):
        if current_user.is_superuser:
            return current_user

        # Get user's permissions through roles
        user_permissions = []
        for user_role in current_user.user_roles:
            for role_perm in user_role.role.role_permissions:
                perm = f"{role_perm.permission.resource}:{role_perm.permission.action}"
                user_permissions.append(perm)

        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {required_permission}",
            )

        return current_user

    return permission_checker


# async def get_current_user(
#     token: Annotated[str, Depends(oauth2_scheme)],
#     session: SessionDep,
# ) -> dict[str, Any]:
#     token_data = await verify_token(token, TokenType.ACCESS, session)
#     if not token_data:
#         raise UnauthorizedException("User not authenticated.")

#     stmt = select(User).where(User.is_deleted.is_(False))

#     if "@" in token_data.username_or_email:
#         stmt = stmt.where(User.email == token_data.username_or_email)
#     else:
#         stmt = stmt.where(User.username == token_data.username_or_email)

#     result = await session.execute(stmt)
#     user = result.scalars().one_or_none()

#     if not user:
#         raise UnauthorizedException("User not authenticated.")

#     return user
