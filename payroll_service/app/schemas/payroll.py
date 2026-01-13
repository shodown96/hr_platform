from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum as PyEnum


class PaymentFrequencyEnum(str, PyEnum):
    WEEKLY = "weekly"
    BI_WEEKLY = "bi_weekly"
    MONTHLY = "monthly"
    ANNUAL = "annual"


class PaymentStatusEnum(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SalaryComponentTypeEnum(str, PyEnum):
    BASIC = "basic"
    BONUS = "bonus"
    OVERTIME = "overtime"
    ALLOWANCE = "allowance"
    COMMISSION = "commission"
    DEDUCTION = "deduction"
    TAX = "tax"
    BENEFIT = "benefit"


# Employee Salary Schemas
class EmployeeSalaryBase(BaseModel):
    employee_id: str
    basic_salary: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    payment_frequency: PaymentFrequencyEnum


class EmployeeSalaryCreate(EmployeeSalaryBase):
    effective_from: date


class EmployeeSalaryUpdate(BaseModel):
    basic_salary: Optional[float] = None
    payment_frequency: Optional[PaymentFrequencyEnum] = None
    effective_from: Optional[date] = None


class EmployeeSalaryResponse(EmployeeSalaryBase):
    id: str
    effective_from: date
    effective_to: Optional[date]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Salary Component Schemas
class SalaryComponentBase(BaseModel):
    component_type: SalaryComponentTypeEnum
    amount: float
    description: Optional[str] = None


class SalaryComponentCreate(SalaryComponentBase):
    pass


class SalaryComponentResponse(SalaryComponentBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Payroll Record Schemas
class PayrollRecordBase(BaseModel):
    employee_id: str
    pay_period_start: date
    pay_period_end: date


class PayrollRecordCreate(PayrollRecordBase):
    components: List[SalaryComponentCreate] = []


class PayrollRecordUpdate(BaseModel):
    payment_status: Optional[PaymentStatusEnum] = None
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


class PayrollRecordResponse(PayrollRecordBase):
    id: str
    employee_salary_id: str
    gross_salary: float
    total_deductions: float
    net_salary: float
    payment_date: Optional[date]
    payment_method: Optional[str]
    payment_reference: Optional[str]
    payment_status: PaymentStatusEnum
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PayrollRecordWithComponents(PayrollRecordResponse):
    salary_components: List[SalaryComponentResponse]


class PayrollSummary(BaseModel):
    """Summary for payroll dashboard"""
    total_employees: int
    total_gross_salary: float
    total_deductions: float
    total_net_salary: float
    pending_count: int
    completed_count: int

