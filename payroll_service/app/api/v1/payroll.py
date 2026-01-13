from datetime import date
from typing import List, Optional

from app.core.db import SessionDep
from app.core.dependencies.auth import check_permission, get_current_user_from_token
from app.services.payroll import EmployeeSalaryService, PayrollService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from schemas.payroll import (
    EmployeeSalaryCreate,
    EmployeeSalaryResponse,
    EmployeeSalaryUpdate,
    PayrollRecordCreate,
    PayrollRecordResponse,
    PayrollRecordUpdate,
    PayrollRecordWithComponents,
    PayrollSummary,
)

from hr_shared.auth.jwt_utils import TokenData

router = APIRouter(prefix="/api/v1/payroll", tags=["payroll"])


# Employee Salary Endpoints


@router.post(
    "/salaries",
    response_model=EmployeeSalaryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee_salary(
    salary_data: EmployeeSalaryCreate,
    db: SessionDep,
    current_user: TokenData = Depends(check_permission("payroll:write")),
):
    """Create or update employee salary"""
    salary = await EmployeeSalaryService.create_employee_salary(db, salary_data)
    return salary


@router.get("/salaries/employee/{employee_id}", response_model=EmployeeSalaryResponse)
async def get_employee_current_salary(
    employee_id: str,
    db: SessionDep,
    current_user: TokenData = Depends(check_permission("payroll:read")),
):
    """Get current salary for employee"""
    salary = await EmployeeSalaryService.get_employee_salary(db, employee_id)
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No salary record found for employee",
        )
    return salary


@router.get(
    "/salaries/employee/{employee_id}/history",
    response_model=List[EmployeeSalaryResponse],
)
async def get_employee_salary_history(
    employee_id: str,
    db: SessionDep,
    current_user: TokenData = Depends(check_permission("payroll:read")),
):
    """Get salary history for employee"""
    salaries = await EmployeeSalaryService.get_salary_history(db, employee_id)
    return salaries


# Payroll Record Endpoints


@router.post(
    "/records",
    response_model=PayrollRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payroll_record(
    payroll_data: PayrollRecordCreate,
    db: SessionDep,
    current_user: TokenData = Depends(check_permission("payroll:write")),
):
    """Create payroll record for employee"""
    payroll = await PayrollService.create_payroll_record(db, payroll_data)
    return payroll


@router.get("/records/{payroll_id}", response_model=PayrollRecordWithComponents)
async def get_payroll_record(
    payroll_id: str,
    db: SessionDep,
    current_user: TokenData = Depends(check_permission("payroll:read")),
):
    """Get payroll record by ID"""
    payroll = await PayrollService.get_payroll_record(db, payroll_id)
    if not payroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payroll record not found"
        )
    return payroll


@router.get(
    "/records/employee/{employee_id}", response_model=List[PayrollRecordResponse]
)
async def get_employee_payroll_records(
    db: SessionDep,
    employee_id: str,
    year: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: TokenData = Depends(check_permission("payroll:read")),
):
    """Get payroll records for employee"""
    payrolls = await PayrollService.get_employee_payroll_records(
        db, employee_id, year, skip, limit
    )
    return payrolls


@router.patch("/records/{payroll_id}", response_model=PayrollRecordResponse)
async def update_payroll_record(
    payroll_id: str,
    payroll_data: PayrollRecordUpdate,
    db: SessionDep,
    current_user: TokenData = Depends(check_permission("payroll:write")),
):
    """Update payroll record"""
    payroll = await PayrollService.update_payroll_record(db, payroll_id, payroll_data)
    return payroll


@router.post("/records/{payroll_id}/process", response_model=PayrollRecordResponse)
async def process_payroll_payment(
    payroll_id: str,
    payment_method: str,
    payment_reference: str,
    db: SessionDep,
    current_user: TokenData = Depends(check_permission("payroll:write")),
):
    """Process payment for payroll record"""
    payroll = await PayrollService.process_payment(
        db, payroll_id, payment_method, payment_reference
    )
    return payroll


@router.get("/summary", response_model=PayrollSummary)
async def get_payroll_summary(
    start_date: date,
    end_date: date,
    db: SessionDep,
    current_user: TokenData = Depends(check_permission("payroll:read")),
):
    """Get payroll summary for period"""
    summary = await PayrollService.get_payroll_summary(db, start_date, end_date)
    return summary


# Employee Self-Service


@router.get("/my-payroll", response_model=List[PayrollRecordResponse])
async def get_my_payroll_records(
    db: SessionDep,
    year: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=12),
    current_user: TokenData = Depends(get_current_user_from_token),
):
    """Get own payroll records (employee self-service)"""
    payrolls = await PayrollService.get_employee_payroll_records(
        db, current_user.employee_id, year, skip, limit
    )
    return payrolls


@router.get("/my-salary", response_model=EmployeeSalaryResponse)
async def get_my_current_salary(
    db: SessionDep, current_user: TokenData = Depends(get_current_user_from_token)
):
    """Get own current salary (employee self-service)"""
    salary = await EmployeeSalaryService.get_employee_salary(
        db, current_user.employee_id
    )
    if not salary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No salary record found"
        )
    return salary
