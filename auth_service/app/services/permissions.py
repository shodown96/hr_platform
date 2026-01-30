from app.models.auth import Permission, RolePermission, User, UserPermission
from app.schemas.auth import (
    PermissionCreate,
    UserPermissionResponse,
    PermissionResponse,
)
from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.messaging.rabbitmq import RabbitMQClient
from app.messaging.event_publisher import AuthEventPublisher
from shared.cache.permissions import get_permission_cache


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

    @staticmethod
    async def get_permissions(db: AsyncSession) -> List[PermissionResponse]:
        result = await db.execute(select(Permission))
        permissions = result.scalars().all()
        return permissions

    @staticmethod
    async def get_user_permissions(
        db: AsyncSession, user_id: str
    ) -> List[UserPermissionResponse]:
        result = await db.execute(
            select(UserPermission)
            .where(UserPermission.user_id == user_id)
            .options(selectinload(UserPermission.permission))
        )
        permissions = result.scalars().all()

        return [
            UserPermissionResponse(
                id=r.id,
                user_id=r.user_id,
                created_at=r.created_at,
                updated_at=r.updated_at,
                permission_id=r.permission.id,
                permission=PermissionResponse.model_validate(r.permission),
            )
            for r in permissions
        ]

    @staticmethod
    async def grant_permission_to_user(
        db: AsyncSession, rabbitmq: RabbitMQClient, user_id: str, permission_id: str
    ) -> UserPermission:
        # TEST
        # await db.execute(
        #     delete(UserPermission).where(
        #         UserPermission.user_id == user_id,
        #         UserPermission.permission_id == permission_id,
        #     )
        # )
        # await db.commit()

        result = await db.execute(
            select(UserPermission)
            .options(selectinload(UserPermission.permission))
            .where(
                UserPermission.user_id == user_id,
                UserPermission.permission_id == permission_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permission already assigned to user",
            )

        # TODO: check if a role is assigned already which includes this permission
        user_permission = UserPermission(user_id=user_id, permission_id=permission_id)
        db.add(user_permission)
        await db.commit()
        await db.refresh(user_permission)

        permission_result = await db.execute(
            select(Permission.action, Permission.resource).where(
                Permission.id == permission_id
            )
        )
        action, resource = permission_result.one()
        permission_name = f"{action}:{resource}"

        # Publish event
        await AuthEventPublisher.publish_permission_granted(
            rabbitmq, user_id, permission_id, permission_name
        )
        await AuthEventPublisher.publish_permissions_changed(rabbitmq, user_id)

        # set_user_permissions

        return user_permission

    @staticmethod
    async def remove_permission_from_user(
        db: AsyncSession, rabbitmq: RabbitMQClient, user_id: str, permission_id: str
    ):
        result = await db.execute(
            select(UserPermission).where(
                UserPermission.user_id == user_id,
                UserPermission.permission_id == permission_id,
            )
        )
        user_permission = result.scalar_one_or_none()

        if not user_permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission access not found",
            )

        await db.delete(user_permission)
        await db.commit()

        permission_result = await db.execute(
            select(Permission.action, Permission.resource).where(
                Permission.id == permission_id
            )
        )
        action, resource = permission_result.one()
        permission_name = f"{action}:{resource}"

        # Publish event
        if user_permission:
            await AuthEventPublisher.publish_permission_removed(
                rabbitmq, user_id, permission_id, permission_name
            )
            await AuthEventPublisher.publish_permissions_changed(rabbitmq, user_id)

        # Invalidate cache - user will get fresh permissions on next request
        cache = await get_permission_cache()
        await cache.invalidate_all_for_user(user_id)
