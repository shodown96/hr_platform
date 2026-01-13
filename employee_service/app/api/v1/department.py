from typing import List

from app.core.db import SessionDep
from app.core.dependencies.auth import check_permission, get_current_active_user
from app.schemas.employment import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)
from app.services.department import DepartmentService
from fastapi import APIRouter, Depends, HTTPException, Query, status

router = APIRouter()


@router.post(
    "/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_department(
    department_data: DepartmentCreate,
    db: SessionDep,
    current_user=Depends(check_permission("employee:write")),
):
    """Create a new department"""
    department = await DepartmentService.create_department(db, department_data)
    return department


@router.get("/departments", response_model=List[DepartmentResponse])
async def get_departments(
    db: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    # current_user=Depends(check_permission("employee:read")),
    current_user=Depends(get_current_active_user),
    
):
    """Get all departments"""
    departments = await DepartmentService.get_departments(db, skip, limit)
    return departments


@router.get("/departments/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: str,
    db: SessionDep,
    current_user=Depends(check_permission("employee:read")),
):
    """Get department by ID"""
    department = await DepartmentService.get_department(db, department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )
    return department


@router.patch("/departments/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: str,
    department_data: DepartmentUpdate,
    db: SessionDep,
    current_user=Depends(check_permission("employee:write")),
):
    """Update department"""
    department = await DepartmentService.update_department(
        db, department_id, department_data
    )
    return department
