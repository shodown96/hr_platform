import enum
from datetime import date, datetime
from typing import List, Optional

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
    __tablename__ = "employee_salaries"

    # Required fields first (no defaults)
    employee_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    basic_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_frequency: Mapped[PaymentFrequency] = mapped_column(
        Enum(PaymentFrequency), nullable=False
    )
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)

    # Optional / defaulted fields after
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    payroll_records: Mapped[List["PayrollRecord"]] = relationship(
        "PayrollRecord", back_populates="employee_salary", init=False
    )


class PayrollRecord(BaseModel):
    __tablename__ = "payroll_records"

    # Required fields first (no defaults)
    employee_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    employee_salary_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("employee_salaries.id"), nullable=False
    )
    pay_period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    pay_period_end: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    gross_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    net_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Optional / defaulted fields after
    total_deductions: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, default=None)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default=None)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default=None)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)

    employee_salary: Mapped["EmployeeSalary"] = relationship(
        "EmployeeSalary", back_populates="payroll_records", init=False
    )
    salary_components: Mapped[List["SalaryComponent"]] = relationship(
        "SalaryComponent", back_populates="payroll_record", cascade="all, delete-orphan", init=False
    )


class SalaryComponent(BaseModel):
    __tablename__ = "salary_components"

    # Required fields first (no defaults)
    payroll_record_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("payroll_records.id"), nullable=False
    )
    component_type: Mapped[SalaryComponentType] = mapped_column(
        Enum(SalaryComponentType), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Optional / defaulted fields after
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default=None)

    payroll_record: Mapped["PayrollRecord"] = relationship(
        "PayrollRecord", back_populates="salary_components", init=False
    )
