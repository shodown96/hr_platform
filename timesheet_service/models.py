# import enum
# from datetime import UTC
# from datetime import date
# from datetime import date as date_type
# from datetime import datetime
# from typing import Optional
# from uuid import uuid4

# from sqlalchemy import Date, DateTime, Enum, Integer, Numeric, String, Text
# from sqlalchemy.orm import Mapped, mapped_column


# class AttendanceStatus(str, enum.Enum):
#     PRESENT = "present"
#     ABSENT = "absent"
#     LATE = "late"
#     HALF_DAY = "half_day"
#     ON_LEAVE = "on_leave"


# class LeaveType(str, enum.Enum):
#     VACATION = "vacation"
#     SICK = "sick"
#     PERSONAL = "personal"
#     MATERNITY = "maternity"
#     PATERNITY = "paternity"
#     UNPAID = "unpaid"


# class LeaveRequestStatus(str, enum.Enum):
#     PENDING = "pending"
#     APPROVED = "approved"
#     REJECTED = "rejected"
#     CANCELLED = "cancelled"


# class Attendance(Base):
#     __tablename__ = "attendances"

#     id: Mapped[str] = mapped_column(
#         String(36), primary_key=True, default=lambda: str(uuid4())
#     )
#     employee_id: Mapped[str] = mapped_column(
#         String(36), nullable=False
#     )  # References Employee service
#     date: Mapped[date_type] = mapped_column(Date, nullable=False)
#     clock_in: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
#     clock_out: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
#     total_hours: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
#     status: Mapped[AttendanceStatus] = mapped_column(
#         Enum(AttendanceStatus), nullable=False
#     )
#     notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))
#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC)
#     )


# class LeaveRequest(Base):
#     __tablename__ = "leave_requests"

#     id: Mapped[str] = mapped_column(
#         String(36), primary_key=True, default=lambda: str(uuid4())
#     )
#     employee_id: Mapped[str] = mapped_column(
#         String(36), nullable=False
#     )  # References Employee service
#     leave_type: Mapped[LeaveType] = mapped_column(Enum(LeaveType), nullable=False)
#     start_date: Mapped[date] = mapped_column(Date, nullable=False)
#     end_date: Mapped[date] = mapped_column(Date, nullable=False)
#     total_days: Mapped[int] = mapped_column(Integer, nullable=False)
#     reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
#     status: Mapped[LeaveRequestStatus] = mapped_column(
#         Enum(LeaveRequestStatus), default=LeaveRequestStatus.PENDING
#     )
#     approver_id: Mapped[Optional[str]] = mapped_column(
#         String(36), nullable=True
#     )  # References Employee service
#     requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))
#     approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
#     rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))
#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC)
#     )


# class LeaveBalance(Base):
#     __tablename__ = "leave_balances"

#     id: Mapped[str] = mapped_column(
#         String(36), primary_key=True, default=lambda: str(uuid4())
#     )
#     employee_id: Mapped[str] = mapped_column(
#         String(36), nullable=False
#     )  # References Employee service
#     leave_type: Mapped[LeaveType] = mapped_column(Enum(LeaveType), nullable=False)
#     year: Mapped[int] = mapped_column(Integer, nullable=False)
#     total_days: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
#     used_days: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
#     remaining_days: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))
#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC)
#     )
