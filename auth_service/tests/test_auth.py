import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy import delete

from app.core.config import settings
from app.models.auth import User
from app.services.auth import AuthService


@pytest.mark.asyncio
async def test_user_gets_role_permissions_in_token(
    client: AsyncClient,
    db_session,
):
    print("\n=== START: role → permissions → token test ===")

    print("\n[STEP 0] Seed admin user")
    admin = User(
        username=settings.ADMIN_USERNAME,
        email=settings.ADMIN_EMAIL,
        password_hash=AuthService.hash_password(settings.ADMIN_PASSWORD),
        is_superuser=True,
        is_active=True,
    )

    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    print("Admin created:", admin.username, admin.id)

    admin_token = AuthService.create_access_token(
        data={
            "sub": str(admin.id),
            "username": admin.username,
            "is_superuser": True,
            "permissions": [],
        }
    )

    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    print("\n[STEP 1] Create role")
    role_res = await client.post(
        "/api/v1/auth/roles",
        json={
            "name": "hr_manager",
            "description": "HR Manager role",
        },
        headers=admin_headers,
    )

    print("Role response:", role_res.status_code, role_res.json())
    assert role_res.status_code == 201

    role_id = role_res.json()["id"]

    print("\n[STEP 2] Create permissions")
    permissions = [
        ("employee", "read"),
        ("employee", "write"),
        ("department", "read"),
        ("payroll", "read"),
    ]

    permission_ids = []

    for resource, action in permissions:
        res = await client.post(
            "/api/v1/auth/permissions",
            json={
                "resource": resource,
                "action": action,
            },
            headers=admin_headers,
        )

        print(f"Permission {resource}:{action} →", res.status_code)
        assert res.status_code == 201

        permission_ids.append(res.json()["id"])

    print("\n[STEP 3] Assign permissions to role")
    for permission_id in permission_ids:
        res = await client.post(
            "/api/v1/auth/roles/assign-permission",
            json={
                "role_id": role_id,
                "permission_id": permission_id,
            },
            headers=admin_headers,
        )

        print("Assign permission response:", res.status_code)
        assert res.status_code == 200

    print("\n[STEP 4] Sign up HR user")
    signup_res = await client.post(
        "/api/v1/auth/sign-up",
        json={
            "username": settings.HR_USERNAME,
            "email": settings.HR_EMAIL,
            "password": settings.HR_PASSWORD,
        },
    )

    print("Signup response:", signup_res.status_code, signup_res.json())
    assert signup_res.status_code == 201

    user_id = signup_res.json()["id"]

    print("\n[STEP 5] Assign role to HR user")
    assign_res = await client.post(
        "/api/v1/auth/users/assign-role",
        json={
            "user_id": user_id,
            "role_id": role_id,
        },
        headers=admin_headers,
    )

    print("Assign role response:", assign_res.status_code)
    assert assign_res.status_code == 200

    print("\n[STEP 6] HR user login")
    signin_res = await client.post(
        "/api/v1/auth/sign-in",
        data={
            "username": settings.HR_USERNAME,
            "password": settings.HR_PASSWORD,
        },
    )

    print("Signin response:", signin_res.status_code, signin_res.json())
    assert signin_res.status_code == 200

    hr_token = signin_res.json()["access_token"]

    print("\n[STEP 7] Decode JWT and assert permissions")
    payload = jwt.decode(
        hr_token,
        settings.SECRET_KEY.get_secret_value(),
        algorithms=[settings.ALGORITHM],
    )

    assert payload["sub"] == str(user_id)
    assert payload["is_superuser"] is False

    expected_permissions = {
        "employee:read",
        "employee:write",
        "department:read",
        "payroll:read",
    }

    print("Expected permissions:", expected_permissions)
    print("Actual permissions:", set(payload["permissions"]))

    assert set(payload["permissions"]) == expected_permissions

    hr_headers = {"Authorization": f"Bearer {hr_token}"}

    print("\n[STEP 8] Fetch HR user via /users/me")
    user_me_res = await client.get(
        "/api/v1/users/me",
        headers=hr_headers,
    )

    print("User me response:", user_me_res.status_code, user_me_res.json())
    assert user_me_res.status_code == 200

    print("\n[STEP 9] Admin creates a normal user")
    user_create_res = await client.post(
        "/api/v1/auth/create-user",
        json={
            "username": settings.USER_USERNAME,
            "email": settings.USER_EMAIL,
            "password": settings.USER_PASSWORD,
        },
        headers=admin_headers,
    )

    print("Create user response:", user_create_res.status_code, user_create_res.json())
    assert user_create_res.status_code == 201

    print("\n[STEP 10] Cleanup")
    await db_session.execute(delete(User))
    await db_session.commit()

    print("\n=== SUCCESS: role permissions encoded in token ===")
