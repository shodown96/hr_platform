from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, List, Optional
import bcrypt

from app.core.config import settings
from app.models.auth import Role, RolePermission, User, UserRole, VerificationToken
from app.models.token_blacklist import TokenBlacklist
from app.schemas.auth import (
    TokenData,
    UserCreate,
    UserUpdate,
    TokenType,
    UserWithRoles,
    RoleResponse,
)
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import or_, select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from shared.auth.jwt_utils import JWTManager

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/sign-in")


class AuthService:

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

    # TOKENS
    @staticmethod
    def create_access_token(
        data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        to_encode = data.copy()
        expire = datetime.now(UTC) + (
            expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire, "token_type": TokenType.ACCESS})
        return jwt.encode(
            to_encode,
            settings.SECRET_KEY.get_secret_value(),
            algorithm=settings.ALGORITHM,
        )

    @staticmethod
    async def create_refresh_token(
        data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        expire = datetime.now(UTC).replace(tzinfo=None) + (
            expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        data.update({"exp": expire, "token_type": TokenType.REFRESH})
        return jwt.encode(
            data,
            settings.SECRET_KEY.get_secret_value(),
            algorithm=settings.ALGORITHM,
        )

    # TOKEN VERIFICATION
    @staticmethod
    async def verify_token(
        token: str, expected_token_type: TokenType, db: AsyncSession
    ) -> TokenData | None:

        result = await db.execute(
            select(TokenBlacklist.id).where(TokenBlacklist.token == token)
        )
        if result.scalar_one_or_none():
            return None

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY.get_secret_value(),
                algorithms=[settings.ALGORITHM],
            )

            if payload.get("token_type") != expected_token_type:
                return None

            user_id = payload.get("sub")
            if not user_id:
                return None

            return TokenData(**payload)

        except JWTError:
            return None

    # BLACKLIST
    @staticmethod
    async def blacklist_tokens(
        access_token: str, refresh_token: str, db: AsyncSession
    ) -> None:

        for token in (access_token, refresh_token):
            payload = jwt.decode(
                token,
                settings.SECRET_KEY.get_secret_value(),
                algorithms=[settings.ALGORITHM],
            )
            exp = payload.get("exp")
            if exp:
                db.add(
                    TokenBlacklist(
                        token=token,
                        expires_at=datetime.fromtimestamp(exp),
                    )
                )

        await db.commit()

    @staticmethod
    async def blacklist_token(token: str, db: AsyncSession) -> None:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
        )
        exp = payload.get("exp")
        if exp:
            db.add(
                TokenBlacklist(
                    token=token,
                    expires_at=datetime.fromtimestamp(exp),
                )
            )
            await db.commit()

    # USERS

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, username: str, password: str
    ) -> Optional[User]:

        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user:
            return None
        if not AuthService.verify_password(password, user.password_hash):
            return None

        user.last_login = datetime.now(UTC)
        await db.commit()

        return user

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        # TEST
        # await db.execute(delete(User))
        await db.execute(delete(User).where(User.is_superuser != True))
        await db.commit()
        result = await db.execute(
            select(User).where(
                or_(
                    User.username == user_data.username,
                    User.email == user_data.email,
                )
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username, email already exists",
            )

        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=AuthService.hash_password(user_data.password),
            is_superuser=(
                user_data.is_superuser if hasattr(user_data, "is_superuser") else None
            ),
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def get_user(db: AsyncSession, user_id: str) -> Optional[UserWithRoles]:
        result = await db.execute(
            select(User)
            .options(joinedload(User.user_roles).joinedload(UserRole.role))
            .where(User.id == user_id)
        )

        user = result.unique().scalar_one_or_none()
        if not user:
            return None

        return UserWithRoles(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=[
                RoleResponse(
                    id=ur.role.id,
                    name=ur.role.name,
                    description=ur.role.description,
                    created_at=ur.role.created_at,
                    updated_at=ur.role.updated_at,
                )
                for ur in user.user_roles
            ],
        )

    async def get_users(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        include_superusers: bool = False,
    ) -> List[UserWithRoles]:
        result = await db.execute(
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .limit(limit)
            .offset(offset)
            .order_by(User.created_at.desc())
        )

        if not include_superusers:
            stmt = stmt.where(User.is_superuser == False)

        users = result.scalars().all()

        return [
            UserWithRoles(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                last_login=user.last_login,
                created_at=user.created_at,
                updated_at=user.updated_at,
                roles=[
                    RoleResponse(
                        id=ur.role.id,
                        name=ur.role.name,
                        description=ur.role.description,
                        created_at=ur.role.created_at,
                        updated_at=ur.role.updated_at,
                    )
                    for ur in user.user_roles
                    if ur.role is not None
                ],
            )
            for user in users
        ]

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:

        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user(
        db: AsyncSession, user_id: str, user_data: UserUpdate
    ) -> User:

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        update_data = user_data.model_dump(exclude_unset=True)

        if "password" in update_data:
            update_data["password_hash"] = AuthService.hash_password(
                update_data.pop("password")
            )

        for field, value in update_data.items():
            setattr(user, field, value)

        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def get_user_permissions(db: AsyncSession, user_id: str) -> List[str]:

        result = await db.execute(
            select(User)
            .options(
                joinedload(User.user_roles)
                .joinedload(UserRole.role)
                .joinedload(Role.role_permissions)
                .joinedload(RolePermission.permission)
            )
            .where(User.id == user_id)
        )

        user = result.unique().scalar_one_or_none()
        if not user:
            return []

        permissions = {
            f"{rp.permission.resource}:{rp.permission.action}"
            for ur in user.user_roles
            for rp in ur.role.role_permissions
        }

        return list(permissions)

    # TODO: implement this, probably redundant
    @staticmethod
    async def authenticate_and_create_token(
        db: AsyncSession, username: str, password: str
    ) -> tuple[str, User]:
        """Authenticate user and create JWT with permissions"""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # Get user with roles and permissions
        stmt = (
            select(User)
            .options(
                selectinload(User.user_roles)
                .selectinload(UserRole.role)
                .selectinload(Role.role_permissions)
                .selectinload(RolePermission.permission)
            )
            .where(User.username == username)
        )

        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not AuthService.verify_password(password, user.password_hash):
            return None, None

        # Collect all permissions from user's roles
        permissions = set()
        for user_role in user.user_roles:
            for role_perm in user_role.role.role_permissions:
                perm_string = (
                    f"{role_perm.permission.resource}:{role_perm.permission.action}"
                )
                permissions.add(perm_string)

        # Create JWT token with permissions
        jwt_manager = JWTManager(
            secret_key=settings.SECRET_KEY.get_secret_value(),
            algorithm=settings.ALGORITHM,
        )

        access_token = jwt_manager.create_token(
            user_id=str(user.id),
            username=user.username,
            is_superuser=user.is_superuser,
            permissions=list(permissions),
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        # Update last login
        user.last_login = datetime.now(UTC)
        await db.commit()

        return access_token, user


 
    @staticmethod
    async def request_reset(db: AsyncSession, email: str) -> VerificationToken:
        """Send OTP for password reset"""
        
        # Check if user exists
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            # Don't reveal if email exists
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="If email exists, OTP has been sent"
            )
        
        # Delete old OTPs for this email
        stmt = delete(VerificationToken).where(VerificationToken.email == email)
        await db.execute(stmt)
        
        # Create new OTP
        token = VerificationToken(
            email=email,
            otp_code=VerificationToken.generate_otp()
        )
        
        db.add(token)
        await db.commit()
        await db.refresh(token)
        
        return token
    
    @staticmethod
    async def verify_and_reset(
        db: AsyncSession,
        email: str,
        otp_code: str,
        new_password: str
    ) -> User:
        """Verify OTP and reset password"""
        
        # Find OTP
        stmt = select(VerificationToken).where(
            and_(
                VerificationToken.email == email,
                VerificationToken.otp_code == otp_code
            )
        ).order_by(VerificationToken.created_at.desc())
        
        result = await db.execute(stmt)
        token = result.scalar_one_or_none()
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP code"
            )
        
        # Check if expired (10 minutes)
        if token.is_expired(10):
            await db.delete(token)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired"
            )
        
        # Get user
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update password
        user.password_hash = AuthService.hash_password(new_password)
        
        # Delete used OTP
        await db.delete(token)
        
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> User:
        """Change password for authenticated user"""
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not AuthService.verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.password_hash = AuthService.hash_password(new_password)
        
        await db.commit()
        await db.refresh(user)
        
        return user

