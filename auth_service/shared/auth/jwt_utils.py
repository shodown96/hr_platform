from datetime import datetime, timedelta, UTC
from typing import Optional, List
from jose import JWTError, jwt
from pydantic import BaseModel


class TokenData(BaseModel):
    """Data stored in JWT token"""

    user_id: str
    username: str
    is_superuser: bool
    permissions: List[str] = []
    exp: Optional[datetime] = None


class JWTManager:
    """Shared JWT token management"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_token(
        self,
        user_id: str,
        username: str,
        is_superuser: bool,
        permissions: List[str],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create JWT access token"""
        to_encode = {
            "sub": user_id,
            "username": username,
            "is_superuser": is_superuser,
            "permissions": permissions,
        }

        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=30)

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            token_data = TokenData(
                user_id=payload.get("sub"),
                username=payload.get("username"),
                is_superuser=payload.get("is_superuser", False),
                permissions=payload.get("permissions", []),
                exp=datetime.fromtimestamp(payload.get("exp")),
            )

            return token_data
        except JWTError:
            return None
