import enum
from datetime import date
from typing import List, Optional

from sqlalchemy import JSON, Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class EmploymentStatus(str, enum.Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class Department(BaseModel):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_department_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("departments.id"), nullable=True
    )

    # Relationships
    parent_department: Mapped[Optional["Department"]] = relationship(
        "Department", remote_side="Department.id", back_populates="sub_departments", init=False
    )
    sub_departments: Mapped[List["Department"]] = relationship(
        "Department", back_populates="parent_department", init=False
    )
    positions: Mapped[List["Position"]] = relationship(
        "Position", back_populates="department", init=False
    )
    employees: Mapped[List["Employee"]] = relationship(
        "Employee", back_populates="department", init=False
    )


class Position(BaseModel):
    __tablename__ = "positions"

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    department_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("departments.id"), nullable=False
    )

    # Relationships
    department: Mapped["Department"] = relationship(
        "Department", back_populates="positions", init=False
    )
    employees: Mapped[List["Employee"]] = relationship(
        "Employee", back_populates="position", init=False
    )


class Employee(BaseModel):
    __tablename__ = "employees"

    user_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[Gender]] = mapped_column(Enum(Gender), nullable=True)
    address: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    termination_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType), nullable=False
    )
    department_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("departments.id"), nullable=False
    )
    position_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("positions.id"), nullable=False
    )
    manager_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("employees.id"), nullable=True
    )

    # Relationships
    department: Mapped["Department"] = relationship(
        "Department", back_populates="employees", init=False
    )
    position: Mapped["Position"] = relationship("Position", back_populates="employees", init=False)
    manager: Mapped[Optional["Employee"]] = relationship(
        "Employee", remote_side="Employee.id", back_populates="subordinates", init=False
    )
    subordinates: Mapped[List["Employee"]] = relationship(
        "Employee", back_populates="manager", init=False
    )
    employment_status: Mapped[EmploymentStatus] = mapped_column(
        Enum(EmploymentStatus), default=EmploymentStatus.ACTIVE
    )
