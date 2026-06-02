import httpx
from typing import Dict, Any


class EmployeeServiceClient:
    """HTTP client to communicate with Employee Service"""

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout

    async def get_employee(self, employee_id: str, auth_token: str) -> Dict[str, Any]:
        """Get employee details by employee ID"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/employees/{employee_id}",
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            response.raise_for_status()
            return response.json()

    async def get_my_profile(self, auth_token: str) -> Dict[str, Any]:
        """Get the current user's employee profile (resolves user_id → employee record)"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/employees/me/profile",
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            response.raise_for_status()
            return response.json()
