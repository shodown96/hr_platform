import httpx
from typing import Optional, Dict, Any


class AuthServiceClient:
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
    
    async def create_user_account(
        self,
        employee_id: str,
        username: str,
        email: str,
        password: str,
        auth_token: str
    ) -> Dict[str, Any]:
        """Create user account in Auth service"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/auth/create-user",
                json={
                    "employee_id": employee_id,
                    "username": username,
                    "email": email,
                    "password": password,
                    "is_superuser": False
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def verify_employee_exists(
        self,
        employee_id: str,
        auth_token: str
    ) -> bool:
        """Verify if employee has user account"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/employee/{employee_id}",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                return response.status_code == 200
            except httpx.HTTPStatusError:
                return False

