from typing import List, Optional

from fastapi import HTTPException, status
from app.schemas.employment import DepartmentCreate, DepartmentUpdate
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employment import Department, Position, Employee


class DepartmentService:

    @staticmethod
    async def create_department(
        db: AsyncSession, department_data: DepartmentCreate
    ) -> Department:
        """Create a new department"""

        # TEST
        await db.execute(delete(Employee))
        await db.execute(delete(Position))
        await db.execute(delete(Department))
        await db.commit()

        # Check if department with same name exists
        stmt = select(Department).where(Department.name == department_data.name)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department with this name already exists",
            )

        # Check parent department exists if provided
        if department_data.parent_department_id:
            parent_stmt = select(Department).where(
                Department.id == department_data.parent_department_id
            )
            parent_result = await db.execute(parent_stmt)
            if not parent_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent department not found",
                )

        department = Department(**department_data.model_dump())
        db.add(department)
        await db.commit()
        await db.refresh(department)

        return department

    @staticmethod
    async def get_department(
        db: AsyncSession, department_id: str
    ) -> Optional[Department]:
        """Get department by ID"""
        stmt = select(Department).where(Department.id == department_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_departments(
        db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Department]:
        """Get all departments"""
        stmt = select(Department).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def update_department(
        db: AsyncSession, department_id: str, department_data: DepartmentUpdate
    ) -> Department:
        """Update department"""
        stmt = select(Department).where(Department.id == department_id)
        result = await db.execute(stmt)
        department = result.scalar_one_or_none()

        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
            )

        update_data = department_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(department, field, value)

        await db.commit()
        await db.refresh(department)

        return department
