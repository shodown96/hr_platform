from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Callable
from datetime import datetime, UTC

from auth.jwt_utils import JWTManager, TokenData


def create_auth_dependencies(
    auth_service_url: str,
    secret_key: str,
    algorithm: str = "HS256"
):
    """
    Factory function to create auth dependencies with specific config
    Each service calls this with their own settings
    """
    
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{auth_service_url}/api/v1/auth/sign-in")
    jwt_manager = JWTManager(secret_key=secret_key, algorithm=algorithm)
    
    async def get_current_user_from_token(
        token: str = Depends(oauth2_scheme)
    ) -> TokenData:
        """Validate JWT token and extract user data"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        token_data = jwt_manager.verify_token(token)
        
        if token_data is None:
            raise credentials_exception
        
        if token_data.exp and token_data.exp < datetime.now(UTC):
            raise credentials_exception
        
        return token_data
    
    async def get_current_active_user(
        token_data: TokenData = Depends(get_current_user_from_token)
    ) -> TokenData:
        """Ensure user is active"""
        return token_data
    
    def check_permission(required_permission: str) -> Callable:
        """Check if user has specific permission"""
        async def permission_checker(
            token_data: TokenData = Depends(get_current_user_from_token)
        ) -> TokenData:
            if token_data.is_superuser:
                return token_data
            
            if required_permission not in token_data.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required: {required_permission}"
                )
            
            return token_data
        
        return permission_checker
    
    return {
        "get_current_user_from_token": get_current_user_from_token,
        "get_current_active_user": get_current_active_user,
        "check_permission": check_permission,
    }
