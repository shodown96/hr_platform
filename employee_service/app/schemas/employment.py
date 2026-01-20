from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmploymentStatusEnum(str, Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"


class EmploymentTypeEnum(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"


class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


# Department Schemas
class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    parent_department_id: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_department_id: Optional[str] = None


class DepartmentResponse(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


# Position Schemas
class PositionBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    level: Optional[str] = None
    department_id: str


class PositionCreate(PositionBase):
    pass


class PositionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    level: Optional[str] = None
    department_id: Optional[str] = None


class PositionResponse(PositionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


# Employee Schemas
class EmployeeBase(BaseModel):
    user_id: str = Field(example="550e8400-e29b-41d4-a716-446655440000")
    employee_code: str = Field(min_length=3, max_length=50, example="EMP001")
    first_name: str = Field(min_length=1, max_length=100, example="John")
    last_name: str = Field(min_length=1, max_length=100, example="Doe")
    middle_name: Optional[str] = Field(None, example="Michael")
    email: EmailStr = Field(example="john.doe@company.com")
    phone_number: Optional[str] = Field(None, example="+1-555-123-4567")
    date_of_birth: Optional[date] = Field(None, example="1990-05-15")
    gender: Optional[GenderEnum] = Field(None, example="male")
    address: Optional[dict] = Field(
        None,
        example={
            "street": "123 Main Street",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "country": "USA",
        },
    )


class EmployeeCreate(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)
    hire_date: date = Field(example="2026-01-20")
    employment_type: EmploymentTypeEnum = Field(example="full_time")
    department_id: Optional[str] = Field(None)
    position_id: Optional[str] = Field(None)
    manager_id: Optional[str] = Field(None)
    termination_date: Optional[date] = Field(None, example="2027-12-31")


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    address: Optional[dict] = None
    employment_status: Optional[EmploymentStatusEnum] = None
    employment_type: Optional[EmploymentTypeEnum] = None
    department_id: Optional[str] = None
    position_id: Optional[str] = None
    manager_id: Optional[str] = None
    termination_date: Optional[date] = None


class EmployeeResponse(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    hire_date: date
    termination_date: Optional[date]
    employment_status: EmploymentStatusEnum
    employment_type: EmploymentTypeEnum
    department_id: Optional[str]
    position_id: Optional[str]
    manager_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class EmployeeWithRelations(EmployeeResponse):
    department: DepartmentResponse
    position: PositionResponse
    manager: Optional[EmployeeResponse] = None
