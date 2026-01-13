
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


class EmployeeEvent(BaseModel):
    """Base event schema for employee-related events"""
    event_id: str
    event_type: Literal[
        "employee.created",
        "employee.updated", 
        "employee.terminated",
        "employee.department_changed"
    ]
    timestamp: datetime
    user_id: str
    employee_id: str
    employee_code: str
    employee_email: str


class EmployeeCreatedEvent(EmployeeEvent):
    """Event published when employee is created"""
    event_type: Literal["employee.created"] = "employee.created"
    first_name: str
    last_name: str
    hire_date: str
    department_id: str
    position_id: str


class EmployeeUpdatedEvent(EmployeeEvent):
    """Event published when employee is updated"""
    event_type: Literal["employee.updated"] = "employee.updated"
    updated_fields: dict


class EmployeeTerminatedEvent(EmployeeEvent):
    """Event published when employee is terminated"""
    event_type: Literal["employee.terminated"] = "employee.terminated"
    termination_date: str
    reason: Optional[str] = None