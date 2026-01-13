import enum
from datetime import date, datetime
from typing import List, Optional
from uuid import uuid4

from app.models.base import BaseModel
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentFrequency(str, enum.Enum):
    WEEKLY = "weekly"
    BI_WEEKLY = "bi_weekly"
    MONTHLY = "monthly"
    ANNUAL = "annual"


class SalaryComponentType(str, enum.Enum):
    BASIC = "basic"
    BONUS = "bonus"
    OVERTIME = "overtime"
    ALLOWANCE = "allowance"
    COMMISSION = "commission"
    DEDUCTION = "deduction"
    TAX = "tax"
    BENEFIT = "benefit"


class EmployeeSalary(BaseModel):
    """
    Stores current and historical salary information for employees
    Each time salary changes, create a new record with new effective dates
    """

    __tablename__ = "employee_salaries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    employee_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Salary amount
    basic_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Payment frequency
    payment_frequency: Mapped[PaymentFrequency] = mapped_column(
        Enum(PaymentFrequency), nullable=False
    )

    # Effective dates
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    payroll_records: Mapped[List["PayrollRecord"]] = relationship(
        "PayrollRecord", back_populates="employee_salary"
    )


class PayrollRecord(BaseModel):
    """
    Individual payroll record for a specific pay period
    Generated for each employee each pay period
    """

    __tablename__ = "payroll_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    employee_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    employee_salary_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("employee_salaries.id"), nullable=False
    )

    # Pay period
    pay_period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    pay_period_end: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Salary calculations
    gross_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_deductions: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    net_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Payment details
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    employee_salary: Mapped["EmployeeSalary"] = relationship(
        "EmployeeSalary", back_populates="payroll_records"
    )
    salary_components: Mapped[List["SalaryComponent"]] = relationship(
        "SalaryComponent", back_populates="payroll_record", cascade="all, delete-orphan"
    )


class SalaryComponent(BaseModel):
    """
    Individual components that make up the total payroll
    Examples: Basic salary, bonus, tax, insurance deduction
    """

    __tablename__ = "salary_components"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    payroll_record_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("payroll_records.id"), nullable=False
    )

    component_type: Mapped[SalaryComponentType] = mapped_column(
        Enum(SalaryComponentType), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    payroll_record: Mapped["PayrollRecord"] = relationship(
        "PayrollRecord", back_populates="salary_components"
    )
