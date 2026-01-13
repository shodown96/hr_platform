from typing import Optional

from app.models.auth import Role, RolePermission, UserRole
from app.schemas.auth import RoleCreate
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


class RoleService:

    @staticmethod
    async def create_role(db: AsyncSession, role_data: RoleCreate) -> Role:
        result = await db.execute(select(Role).where(Role.name == role_data.name))
        existing_role = result.scalar_one_or_none()

        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role with this name already exists",
            )

        role = Role(**role_data.model_dump())
        db.add(role)
        await db.commit()
        await db.refresh(role)

        return role

    @staticmethod
    async def get_role(db: AsyncSession, role_id: str) -> Optional[Role]:
        result = await db.execute(
            select(Role)
            .options(
                joinedload(Role.role_permissions).joinedload(RolePermission.permission)
            )
            .where(Role.id == role_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def assign_role_to_user(
        db: AsyncSession, user_id: str, role_id: str
    ) -> UserRole:
        result = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role already assigned to user",
            )

        user_role = UserRole(user_id=user_id, role_id=role_id)
        db.add(user_role)
        await db.commit()
        await db.refresh(user_role)

        return user_role

    @staticmethod
    async def remove_role_from_user(db: AsyncSession, user_id: str, role_id: str):
        result = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        )
        user_role = result.scalar_one_or_none()

        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role assignment not found",
            )

        await db.delete(user_role)
        await db.commit()
