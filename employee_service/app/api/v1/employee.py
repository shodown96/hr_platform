from datetime import date
from typing import List, Optional

import httpx
from app.core.db import SessionDep
from app.core.dependencies.auth import check_permission, get_current_user_from_token
from app.core.shared.auth.jwt_utils import TokenData
from app.messaging.rabbitmq import RabbitMQDep
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    EmployeeWithRelations,
    TerminationRequest,
)
from app.services.employee import EmployeeService
from fastapi import APIRouter, Depends, HTTPException, Query, status

router = APIRouter()


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    db: SessionDep,
    rabbitmq: RabbitMQDep,
    current_user=Depends(check_permission("employee:write")),
):
    """Create a new employee"""
    employee = await EmployeeService.create_employee(db, rabbitmq, employee_data)
    return employee


@router.post(
    "/sign-up", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED
)
async def continue_user_signup(
    employee_data: EmployeeCreate,
    db: SessionDep,
    rabbitmq: RabbitMQDep,
    current_user: TokenData = Depends(get_current_user_from_token),
):
    """Create employee details for just signed up user"""
    # payload = employee_data.model_copy(update={"user_id": current_user.user_id})
    # employee = await EmployeeService.create_employee(db, payload)
    employee_data.user_id = current_user.user_id
    employee = await EmployeeService.create_employee(db, rabbitmq, employee_data)
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
    payload: TerminationRequest,
    db: SessionDep,
    rabbitmq: RabbitMQDep,
    current_user=Depends(check_permission("employee:write")),
):
    """Terminate an employee"""
    employee = await EmployeeService.terminate_employee(db, rabbitmq, payload)
    return employee


@router.get("/me/profile", response_model=EmployeeWithRelations)
async def get_my_profile(
    db: SessionDep, current_user: TokenData = Depends(get_current_user_from_token)
):
    """
    Get current user's employee profile
    Any authenticated user can access their own profile
    """
    employee = await EmployeeService.get_employee_by_user_id(
        db, current_user.user_id, include_relations=True
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found"
        )

    return employee
