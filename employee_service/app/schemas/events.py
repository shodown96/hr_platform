from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class EmployeeEvent(BaseModel):
    event_id: str
    event_type: Literal[
        "employee.created",
        "employee.updated",
        "employee.terminated",
        "employee.department.changed",
        "employee.position.changed",
    ]
    timestamp: datetime
    user_id: str
    employee_id: str
    employee_code: str
    employee_email: str


class EmployeeCreatedEvent(EmployeeEvent):
    event_type: Literal["employee.created"] = "employee.created"
    first_name: str
    last_name: str
    hire_date: str
    department_id: Optional[str] = None
    position_id: Optional[str] = None


class EmployeeUpdatedEvent(EmployeeEvent):
    event_type: Literal["employee.updated"] = "employee.updated"
    updated_fields: dict


class EmployeeTerminatedEvent(EmployeeEvent):
    event_type: Literal["employee.terminated"] = "employee.terminated"
    termination_date: Optional[str] = None
    reason: Optional[str] = None
