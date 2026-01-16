import httpx
from typing import Dict, Any


class EmployeeServiceClient:
    """HTTP client to communicate with Employee Service"""
    
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
    
    async def get_employee(
        self,
        employee_id: str,
        auth_token: str
    ) -> Dict[str, Any]:
        """Get employee details from Employee Service"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/employees/{employee_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            response.raise_for_status()
            return response.json()
