from app.core.db import SessionDep
from app.core.dependencies.auth import check_permission, get_current_superuser
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import (
    AssignPermissionRequest,
    AssignRoleRequest,
    PermissionCreate,
    PermissionResponse,
    RoleCreate,
    RoleResponse,
    RoleWithPermissions,
    TokenResponse,
    UserCreate,
    UserCreateInternal,
    UserResponse,
)
from app.services.auth import AuthService
from app.services.permissions import PermissionService
from app.services.roles import RoleService
from app.schemas.auth import TokenType
from app.models.auth import User

router = APIRouter()


@router.post(
    "/sign-up", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def sign_up(
    user_data: UserCreate,
    db: SessionDep,
    # dependencies=Depends(anonymous_only),
):
    """Sign up as a new user"""
    user = await AuthService.create_user(db, user_data)
    return user


@router.post(
    "/create-user", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def create_user(
    user_data: UserCreateInternal,
    db: SessionDep,
    current_user: User = Depends(
        get_current_superuser
    ),  # Only superusers can create users
):
    """Create a new user as an admin"""
    user = await AuthService.create_user(db, user_data)
    return user


@router.post("/sign-in", response_model=TokenResponse)
async def sign_in(db: SessionDep, form_data: OAuth2PasswordRequestForm = Depends()):
    """Sign in and get access token"""
    user = await AuthService.authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user permissions
    permissions = await AuthService.get_user_permissions(db, str(user.id))

    # Create access token
    access_token = AuthService.create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "is_superuser": user.is_superuser,
            "permissions": permissions,
        }
    )
    print(user.email)
    return TokenResponse(
        token_type=TokenType.ACCESS,
        access_token=access_token, 
        user=UserResponse.model_validate(user)
    )


# Role Management Endpoints


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    db: SessionDep,
    current_user: User = Depends(get_current_superuser),
):
    """Create a new role"""
    role = await RoleService.create_role(db, role_data)
    return role


@router.get("/roles/{role_id}", response_model=RoleWithPermissions)
async def get_role(
    role_id: str,
    db: SessionDep,
    current_user: User = Depends(check_permission("role:read")),
):
    """Get role by ID"""
    role = await RoleService.get_role(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    return role


@router.post("/users/assign-role", status_code=status.HTTP_200_OK)
async def assign_role_to_user(
    request: AssignRoleRequest,
    db: SessionDep,
    current_user: User = Depends(get_current_superuser),
):
    """Assign role to user"""
    user_role = await RoleService.assign_role_to_user(db, request.user_id, request.role_id)
    return {"message": "Role assigned successfully"}


@router.delete(
    "/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    db: SessionDep,
    current_user: User = Depends(get_current_superuser),
):
    """Remove role from user"""
    await RoleService.remove_role_from_user(db, user_id, role_id)


# Permission Management Endpoints


@router.post(
    "/permissions",
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


@router.post("/roles/assign-permission", status_code=status.HTTP_200_OK)
async def assign_permission_to_role(
    request: AssignPermissionRequest,
    db: SessionDep,
    current_user: User = Depends(get_current_superuser),
):
    """Assign permission to role"""
    role_perm = await PermissionService.assign_permission_to_role(
        db, request.role_id, request.permission_id
    )
    return {"message": "Permission assigned successfully"}


@router.delete(
    "/roles/{role_id}/permissions/{permission_id}",
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
