from app.core.db import SessionDep
from app.core.dependencies.auth import check_permission, get_current_superuser
from app.messaging.rabbitmq import RabbitMQDep
from app.models.auth import User
from app.schemas.auth import (
    AssignPermissionToRoleRequest,
    AssignPermissionToUserRequest,
    PermissionCreate,
    PermissionResponse,
    UserPermissionResponse,
)
from app.services.permissions import PermissionService
from app.services.auth import AuthService
from fastapi import APIRouter, Depends, status
from typing import List
from app.core.shared.cache.permissions import PermissionsDep

router = APIRouter()


# Permission Management Endpoints
@router.post(
    "/",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_permission(
    permission_data: PermissionCreate,
    db: SessionDep,
    current_user: User = Depends(get_current_superuser),
):
    """Create a new permission"""
    permission = await PermissionService.create_permission(db, permission_data)
    return permission


#  Get permissions
@router.get("/", response_model=List[PermissionResponse])
async def get_permissions(
    db: SessionDep,
    current_user: User = Depends(check_permission("role:read")),
):
    """Get available permissions"""
    roles = await PermissionService.get_permissions(db)

    return roles


@router.get("/user-permissions/{user_id}", response_model=List[UserPermissionResponse])
async def get_user_permissions(
    user_id: str,
    cache: PermissionsDep,
    db: SessionDep,
    current_user: User = Depends(check_permission("role:read")),
):
    """Get user permissions"""
    permissions = await AuthService.get_user_permissions(db, cache, user_id)

    return permissions


@router.post("/assign-permission-to-role", status_code=status.HTTP_200_OK)
async def assign_permission_to_role(
    body: AssignPermissionToRoleRequest,
    db: SessionDep,
    current_user: User = Depends(get_current_superuser),
):
    """Assign permission to role"""
    role_perm = await PermissionService.assign_permission_to_role(
        db, body.role_id, body.permission_id
    )
    return {"message": "Permission assigned successfully"}


@router.delete(
    "/remove-permission-from-role/{role_id}/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_permission_from_role(
    role_id: str,
    permission_id: str,
    db: SessionDep,
    current_user: User = Depends(get_current_superuser),
):
    """Remove permission from role"""
    await PermissionService.remove_permission_from_role(db, role_id, permission_id)
    return {"message": "Permission removed successfully"}


@router.post("/grant-permission-to-user", status_code=status.HTTP_200_OK)
async def grant_permission_to_user(
    body: AssignPermissionToUserRequest,
    db: SessionDep,
    cache: PermissionsDep,
    rabbitmq: RabbitMQDep,
    current_user: User = Depends(get_current_superuser),
):
    """Assign permission to role"""
    role_perm = await PermissionService.grant_permission_to_user(
        db, rabbitmq, body.user_id, body.permission_id
    )
    # Get user permissions
    permissions = await AuthService.get_user_permissions(db, cache, body.user_id)
    return {"message": "Permission assigned successfully"}


@router.delete(
    "/remove-permission-from-user/{user_id}/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_permission_from_role(
    permission_id: str,
    user_id: str,
    rabbitmq: RabbitMQDep,
    db: SessionDep,
    current_user: User = Depends(get_current_superuser),
):
    """Remove permission from user"""
    await PermissionService.remove_permission_from_user(
        db, rabbitmq, user_id, permission_id
    )

    return {"message": "Permission removed successfully"}
