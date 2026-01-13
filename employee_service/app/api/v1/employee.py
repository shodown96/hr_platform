from datetime import date
from typing import List, Optional

import httpx
from app.core.db import SessionDep
from app.core.dependencies.auth import check_permission, get_current_user_from_token
from app.schemas.employment import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    EmployeeWithRelations,
)
from app.services.employee import EmployeeService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.messaging.rabbitmq import RabbitMQDep
from shared.auth.jwt_utils import TokenData

router = APIRouter()


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    db: SessionDep,
    current_user=Depends(check_permission("employee:write")),
):
    """Create a new employee"""
    employee = await EmployeeService.create_employee(db, employee_data)
    return employee


@router.get("/", response_model=List[EmployeeResponse])
async def get_employees(
    db: SessionDep,
    department_id: Optional[str] = None,
    position_id: Optional[str] = None,
    manager_id: Optional[str] = None,
    employment_status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user=Depends(check_permission("employee:read")),
):
    """Get employees with optional filters"""
    employees = await EmployeeService.get_employees(
        db, department_id, position_id, manager_id, employment_status, skip, limit
    )
    return employees


@router.get("/{employee_id}", response_model=EmployeeWithRelations)
async def get_employee(
    employee_id: str,
    db: SessionDep,
    current_user=Depends(check_permission("employee:read")),
):
    """Get employee by ID with relationships"""
    employee = await EmployeeService.get_employee(
        db, employee_id, include_relations=True
    )
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )
    return employee


@router.get("/code/{employee_code}", response_model=EmployeeResponse)
async def get_employee_by_code(
    employee_code: str,
    db: SessionDep,
    current_user=Depends(check_permission("employee:read")),
):
    """Get employee by employee code"""
    employee = await EmployeeService.get_employee_by_code(db, employee_code)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )
    return employee


@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    employee_data: EmployeeUpdate,
    db: SessionDep,
    current_user=Depends(check_permission("employee:write")),
):
    """Update employee"""
    employee = await EmployeeService.update_employee(db, employee_id, employee_data)
    return employee


@router.post("/{employee_id}/terminate", response_model=EmployeeResponse)
async def terminate_employee(
    employee_id: str,
    termination_date: date,
    db: SessionDep,
    current_user=Depends(check_permission("employee:write")),
):
    """Terminate an employee"""
    employee = await EmployeeService.terminate_employee(
        db, employee_id, termination_date
    )
    return employee


@router.post(
    "/with-account",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee_with_account(
    employee_data: EmployeeCreate,
    username: str,
    password: str,
    db: SessionDep,
    rabbitmq: RabbitMQDep,
    current_user=Depends(check_permission("employee:write")),
):
    """Create employee and user account in auth service"""
    from app.clients.auth import AuthServiceClient
    from app.core.config import settings

    # 1. Create employee in Employee Management service
    employee = await EmployeeService.create_employee_with_events(
        db, employee_data, rabbitmq
    )

    # 2. Create user account in Auth service
    auth_client = AuthServiceClient(settings.AUTH_SERVICE_URL)
    try:
        await auth_client.create_user_account(
            employee_id=str(employee.id),
            username=username,
            email=employee.email,
            password=password,
            auth_token=current_user.access_token,  # Pass through from request
        )
    except httpx.HTTPError as e:
        # Rollback employee creation if auth service fails
        await db.delete(employee)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user account: {str(e)}",
        )

    return employee


@router.get("/me/profile", response_model=EmployeeWithRelations)
async def get_my_profile(
    db: SessionDep, current_user: TokenData = Depends(get_current_user_from_token)
):
    """
    Get current user's employee profile
    Any authenticated user can access their own profile
    """
    print(current_user.employee_id)
    employee = await EmployeeService.get_employee(
        db, current_user.employee_id, include_relations=True
    )
    print(current_user.employee_id)
    

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found"
        )

    return employee
