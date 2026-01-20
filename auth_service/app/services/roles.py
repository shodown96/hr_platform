from typing import Optional, List

from app.messaging.event_publisher import AuthEventPublisher
from app.messaging.rabbitmq import RabbitMQClient
from app.models.auth import Role, RolePermission, UserRole
from app.schemas.auth import RoleCreate, RoleWithPermissions, PermissionResponse
from fastapi import HTTPException, status
from shared.cache.permissions import get_permission_cache
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload


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
    async def get_roles(db: AsyncSession) -> List[RoleWithPermissions]:
        result = await db.execute(
            select(Role).options(
                selectinload(Role.role_permissions).selectinload(
                    RolePermission.permission
                )
            )
        )
        roles = result.scalars().all()
        return [
            RoleWithPermissions(
                id=r.id,
                name=r.name,
                description=r.description,
                created_at=r.created_at,
                updated_at=r.updated_at,
                permissions=[
                    PermissionResponse.model_validate(rp.permission)
                    for rp in r.role_permissions
                ],
            )
            for r in roles
        ]

    @staticmethod
    async def get_role(db: AsyncSession, role_id: str) -> Optional[RoleWithPermissions]:
        result = await db.execute(
            select(Role)
            .options(
                selectinload(Role.role_permissions).selectinload(
                    RolePermission.permission
                )
            )
            .where(Role.id == role_id)
        )
        role = result.scalar_one_or_none()
        if not role:
            return None
        return RoleWithPermissions(
            id=role.id,
            name=role.name,
            description=role.description,
            created_at=role.created_at,
            updated_at=role.updated_at,
            permissions=[
                PermissionResponse.model_validate(rp.permission)
                for rp in role.role_permissions
            ],
        )

    @staticmethod
    async def assign_role_to_user(
        db: AsyncSession, rabbitmq: RabbitMQClient, user_id: str, role_id: str
    ) -> UserRole:
        # TEST
        # await db.execute(
        #     delete(UserRole).where(
        #         UserRole.user_id == user_id,
        #         UserRole.role_id == role_id,
        #     )
        # )
        result = await db.execute(
            select(UserRole)
            .options(selectinload(UserRole.role))
            .where(
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
        
        role_result = await db.execute(select(Role.name).where(Role.id == role_id))
        role_name = role_result.scalar_one()
        
        # Publish event
        await AuthEventPublisher.publish_role_assigned(
            rabbitmq, user_id, role_id, role_name
        )

        return user_role

    @staticmethod
    async def remove_role_from_user(
        db: AsyncSession, rabbitmq: RabbitMQClient, user_id: str, role_id: str
    ):
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

        # Publish event
        if user_role.role:
            await AuthEventPublisher.publish_role_removed(
                rabbitmq, user_id, role_id, user_role.role.name
            )

        # Invalidate cache
        cache = await get_permission_cache()
        await cache.invalidate_all_for_user(user_id)
