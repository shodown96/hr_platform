from datetime import datetime, timezone

from app.core.config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from shared.auth.jwt_utils import JWTManager, TokenData
from shared.cache.permissions import PermissionCache, get_permission_cache

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.AUTH_SERVICE_URL}/api/v1/auth/sign-in"
)

# Initialize JWT manager with shared secret
jwt_manager = JWTManager(
    secret_key=settings.SECRET_KEY.get_secret_value(), algorithm=settings.ALGORITHM
)


async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme),
    cache: PermissionCache = Depends(get_permission_cache),
) -> TokenData:
    """
    Validate JWT and get permissions

    Flow:
    1. Validate JWT signature
    2. Check if permissions are in cache (fast path)
    3. If not in cache, use permissions from token and cache them
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Validate token
    print("yayyyy")
    token_data = jwt_manager.verify_token(token)

    if token_data is None:
        raise credentials_exception

    # Check if token is expired
    if token_data.exp and token_data.exp.replace(tzinfo=timezone.utc) < datetime.now(
        timezone.utc
    ):
        raise credentials_exception

    # Check cache for fresh permissions
    cached_permissions = await cache.get_user_permissions(token_data.user_id)

    if cached_permissions is not None:
        # Use cached permissions (more up-to-date)
        print(f"✅ Using cached permissions for user {token_data.user_id}")
        token_data.permissions = cached_permissions
    else:
        # Cache the permissions from token
        print(f"📝 Caching permissions for user {token_data.user_id}")
        await cache.set_user_permissions(token_data.user_id, token_data.permissions)

    return token_data


def check_permission(required_permission: str):
    """Check if user has specific permission"""

    async def permission_checker(
        token_data: TokenData = Depends(get_current_user_from_token),
    ) -> TokenData:
        if token_data.is_superuser:
            return token_data

        if required_permission not in token_data.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {required_permission}",
            )

        return token_data

    return permission_checker


async def get_current_active_user(
    token_data: TokenData = Depends(get_current_user_from_token),
) -> TokenData:
    """Ensure user is active (based on token data)"""
    # In a more robust system, you might call Auth service to verify user is still active
    # For now, we trust the token
    return token_data


async def get_current_superuser(
    token_data: TokenData = Depends(get_current_user_from_token),
) -> TokenData:
    """Ensure user is superuser"""
    if not token_data.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return token_data


def check_any_permission(*required_permissions: str):
    """
    Check if user has ANY of the specified permissions
    """

    async def permission_checker(
        token_data: TokenData = Depends(get_current_user_from_token),
    ) -> TokenData:
        if token_data.is_superuser:
            return token_data

        # Check if user has any of the required permissions
        has_permission = any(
            perm in token_data.permissions for perm in required_permissions
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required one of: {', '.join(required_permissions)}",
            )

        return token_data

    return permission_checker


def check_all_permissions(*required_permissions: str):
    """
    Check if user has ALL of the specified permissions
    """

    async def permission_checker(
        token_data: TokenData = Depends(get_current_user_from_token),
    ) -> TokenData:
        if token_data.is_superuser:
            return token_data

        # Check if user has all required permissions
        missing_permissions = [
            perm for perm in required_permissions if perm not in token_data.permissions
        ]

        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Missing: {', '.join(missing_permissions)}",
            )

        return token_data

    return permission_checker
