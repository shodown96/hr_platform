
from datetime import datetime, UTC
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from shared.auth.jwt_utils import JWTManager, TokenData
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.AUTH_SERVICE_URL}/api/v1/auth/sign-in")

# Initialize JWT manager with shared secret
jwt_manager = JWTManager(
    secret_key=settings.SECRET_KEY.get_secret_value(),
    algorithm=settings.ALGORITHM
)


async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme)
) -> TokenData:
    """
    Validate JWT token and extract user data
    This works without database access - just validates the token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = jwt_manager.verify_token(token)
    
    if token_data is None:
        raise credentials_exception
    
    # Check if token is expired
    exp_dt = datetime.fromtimestamp(token_data.exp.timestamp(), tz=UTC)
    if exp_dt and exp_dt < datetime.now(UTC):
        raise credentials_exception
    
    return token_data


async def get_current_active_user(
    token_data: TokenData = Depends(get_current_user_from_token)
) -> TokenData:
    """Ensure user is active (based on token data)"""
    # In a more robust system, you might call Auth service to verify user is still active
    # For now, we trust the token
    return token_data


async def get_current_superuser(
    token_data: TokenData = Depends(get_current_user_from_token)
) -> TokenData:
    """Ensure user is superuser"""
    if not token_data.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return token_data


def check_permission(required_permission: str):
    """
    Dependency factory to check if user has specific permission
    Works by reading permissions from JWT token
    """
    async def permission_checker(
        token_data: TokenData = Depends(get_current_user_from_token)
    ) -> TokenData:
        # Superusers have all permissions
        if token_data.is_superuser:
            return token_data
        
        # Check if user has the required permission
        if required_permission not in token_data.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {required_permission}"
            )
        
        return token_data
    
    return permission_checker


def check_any_permission(*required_permissions: str):
    """
    Check if user has ANY of the specified permissions
    """
    async def permission_checker(
        token_data: TokenData = Depends(get_current_user_from_token)
    ) -> TokenData:
        if token_data.is_superuser:
            return token_data
        
        # Check if user has any of the required permissions
        has_permission = any(
            perm in token_data.permissions 
            for perm in required_permissions
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required one of: {', '.join(required_permissions)}"
            )
        
        return token_data
    
    return permission_checker


def check_all_permissions(*required_permissions: str):
    """
    Check if user has ALL of the specified permissions
    """
    async def permission_checker(
        token_data: TokenData = Depends(get_current_user_from_token)
    ) -> TokenData:
        if token_data.is_superuser:
            return token_data
        
        # Check if user has all required permissions
        missing_permissions = [
            perm for perm in required_permissions 
            if perm not in token_data.permissions
        ]
        
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Missing: {', '.join(missing_permissions)}"
            )
        
        return token_data
    
    return permission_checker