import pytest
from app.core.config import settings
from httpx import AsyncClient

AUTH_BASE_URL = "http://127.0.0.1:8081"
EMPLOYEE_BASE_URL = "http://127.0.0.1:8000"


@pytest.mark.asyncio
async def test_auth_to_employee_profile_flow():
    print("\n=== START: auth → employee profile integration test ===")

    async with AsyncClient(base_url=AUTH_BASE_URL) as auth_client, AsyncClient(
        base_url=EMPLOYEE_BASE_URL
    ) as employee_client:

        print("\n[STEP 0] Admin sign-in")
        signin_res = await auth_client.post(
            "/api/v1/auth/sign-in",
            data={
                "username": settings.ADMIN_USERNAME,
                "password": settings.ADMIN_PASSWORD,
            },
        )

        print("Admin signin response:", signin_res.status_code)
        assert signin_res.status_code == 200

        admin_token = signin_res.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        print("\n[STEP 1] Sign up employee via Auth service")
        signup_res = await auth_client.post(
            "/api/v1/auth/sign-up",
            json={
                "username": settings.EMPLOYEE_USERNAME,
                "email": settings.EMPLOYEE_EMAIL,
                "password": settings.EMPLOYEE_PASSWORD,
            },
        )

        print("Signup response:", signup_res.status_code)
        assert signup_res.status_code == 201

        print("\n[STEP 2] Employee login via Auth service")
        login_res = await auth_client.post(
            "/api/v1/auth/sign-in",
            data={
                "username": settings.EMPLOYEE_USERNAME,
                "password": settings.EMPLOYEE_PASSWORD,
            },
        )

        print("Login response:", login_res.status_code)
        assert login_res.status_code == 200

        employee_token = login_res.json()["access_token"]
        employee_headers = {"Authorization": f"Bearer {employee_token}"}

        print("\n[STEP 3] Create department (admin)")
        dept_res = await employee_client.post(
            "/api/v1/departments/departments",
            json={"name": "Engineering"},
            headers=admin_headers,
        )

        print("Department response:", dept_res.status_code)
        assert dept_res.status_code == 201

        department_id = dept_res.json()["id"]

        print("\n[STEP 4] Create position (admin)")
        pos_res = await employee_client.post(
            "/api/v1/positions/positions",
            json={
                "title": "HR Manager",
                "department_id": department_id,
            },
            headers=admin_headers,
        )

        print("Position response:", pos_res.status_code)
        assert pos_res.status_code == 201

        position_id = pos_res.json()["id"]

        print("\n[STEP 5] Create employee record (admin)")
        emp_res = await employee_client.post(
            "/api/v1/employees/",
            json={
                "employee_code": settings.EMPLOYEE_CODE,
                "first_name": settings.EMPLOYEE_FIRST_NAME,
                "last_name": settings.EMPLOYEE_LAST_NAME,
                "email": settings.EMPLOYEE_EMAIL,
                "hire_date": "2026-01-01",
                "employment_type": "full_time",
                "department_id": department_id,
                "position_id": position_id,
            },
            headers=admin_headers,
        )

        print("Employee create response:", emp_res.status_code)
        assert emp_res.status_code == 201

        print("\n[STEP 6] Fetch own employee profile")
        profile_res = await employee_client.get(
            "/api/v1/employees/me/profile",
            headers=employee_headers,
        )

        print("Profile response:", profile_res.status_code)
        assert profile_res.status_code == 200

        profile = profile_res.json()

        print("\n[STEP 7] Assertions")
        assert profile["email"] == settings.EMPLOYEE_EMAIL
        assert profile["employee_code"] == settings.EMPLOYEE_CODE
        assert profile["department"]["id"] == department_id
        assert profile["position"]["id"] == position_id

        print("\n=== SUCCESS: integration test completed ===")
