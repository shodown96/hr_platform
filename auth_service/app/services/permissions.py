from app.models.auth import Permission, RolePermission
from app.schemas.auth import PermissionCreate
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class PermissionService:

    @staticmethod
    async def create_permission(
        db: AsyncSession,
        permission_data: PermissionCreate,
    ) -> Permission:
        """Create a new permission"""

        result = await db.execute(
            select(Permission).where(
                Permission.resource == permission_data.resource,
                Permission.action == permission_data.action,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permission already exists",
            )

        permission = Permission(**permission_data.model_dump())
        db.add(permission)
        await db.commit()
        await db.refresh(permission)

        return permission

    @staticmethod
    async def assign_permission_to_role(
        db: AsyncSession,
        role_id: str,
        permission_id: str,
    ) -> RolePermission:
        """Assign permission to role"""

        result = await db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permission already assigned to role",
            )

        role_perm = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
        )
        db.add(role_perm)
        await db.commit()
        await db.refresh(role_perm)

        return role_perm

    @staticmethod
    async def remove_permission_from_role(
        db: AsyncSession,
        role_id: str,
        permission_id: str,
    ) -> None:
        """Remove permission from role"""

        result = await db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )
        role_perm = result.scalar_one_or_none()

        if not role_perm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission assignment not found",
            )

        await db.delete(role_perm)
        await db.commit()
