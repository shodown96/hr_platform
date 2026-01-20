from datetime import date
from typing import List, Optional

from app.messaging.event_publisher import EventPublisher
from app.messaging.rabbitmq import RabbitMQClient
from app.models.employment import Department, Employee, Position
from app.schemas.employment import EmployeeCreate, EmployeeUpdate
from fastapi import HTTPException, status
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class EmployeeService:

    @staticmethod
    async def create_employee(
        db: AsyncSession,
        employee_data: EmployeeCreate,
    ) -> Employee:
        """Create a new employee"""
        # TEST
        # await db.execute(delete(Employee))
        # await db.execute(delete(Position))
        # await db.execute(delete(Department))
        # await db.commit()

        # Check if employee with same email or code exists
        stmt = select(Employee).where(
            or_(
                Employee.user_id == employee_data.user_id,
                Employee.email == employee_data.email,
                Employee.employee_code == employee_data.employee_code,
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee with this user_id, email or employee code already exists",
            )

        # Verify department exists
        if employee_data.position_id:
            dept_stmt = select(Department).where(
                Department.id == employee_data.department_id
            )
            dept_result = await db.execute(dept_stmt)
            if not dept_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
                )

        # Verify position exists
        if employee_data.position_id:
            pos_stmt = select(Position).where(Position.id == employee_data.position_id)
            pos_result = await db.execute(pos_stmt)
            if not pos_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Position not found"
                )

        # Verify manager exists if provided
        if employee_data.manager_id:
            mgr_stmt = select(Employee).where(Employee.id == employee_data.manager_id)
            mgr_result = await db.execute(mgr_stmt)
            if not mgr_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Manager not found"
                )
        statement = select(func.count()).select_from(Employee)
        result = await db.execute(statement)
        count: int = result.scalar()
        employee_data.employee_code = f"EMP{count:05}"
        print("employee_data", employee_data)
        employee = Employee(**employee_data.model_dump())
        db.add(employee)
        await db.commit()
        await db.refresh(employee)

        return employee

    @staticmethod
    async def get_employee(
        db: AsyncSession, employee_id: str, include_relations: bool = False
    ) -> Optional[Employee]:
        """Get employee by ID with optional relationships"""
        stmt = select(Employee).where(Employee.id == employee_id)

        if include_relations:
            stmt = stmt.options(
                selectinload(Employee.department),
                selectinload(Employee.position),
                selectinload(Employee.manager),
            )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_employee_by_user_id(
        db: AsyncSession, user_id: str, include_relations: bool = False
    ) -> Optional[Employee]:
        """Get employee by ID with optional relationships"""
        stmt = select(Employee).where(Employee.user_id == user_id)

        if include_relations:
            stmt = stmt.options(
                selectinload(Employee.department),
                selectinload(Employee.position),
                selectinload(Employee.manager),
            )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_employee_by_code(
        db: AsyncSession, employee_code: str, include_relations: bool = False
    ) -> Optional[Employee]:
        """Get employee by employee code"""
        stmt = select(Employee).where(Employee.employee_code == employee_code)

        if include_relations:
            stmt = stmt.options(
                selectinload(Employee.department),
                selectinload(Employee.position),
                selectinload(Employee.manager),
            )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_employee_by_email(db: AsyncSession, email: str) -> Optional[Employee]:
        """Get employee by email"""
        stmt = select(Employee).where(Employee.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_employees(
        db: AsyncSession,
        department_id: Optional[str] = None,
        position_id: Optional[str] = None,
        manager_id: Optional[str] = None,
        employment_status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Employee]:
        """Get employees with optional filters"""
        stmt = select(Employee)

        conditions = []
        if department_id:
            conditions.append(Employee.department_id == department_id)
        if position_id:
            conditions.append(Employee.position_id == position_id)
        if manager_id:
            conditions.append(Employee.manager_id == manager_id)
        if employment_status:
            conditions.append(Employee.employment_status == employment_status)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def update_employee(
        db: AsyncSession, employee_id: str, employee_data: EmployeeUpdate
    ) -> Employee:
        """Update employee"""
        stmt = select(Employee).where(Employee.id == employee_id)
        result = await db.execute(stmt)
        employee = result.scalar_one_or_none()

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
            )

        update_data = employee_data.model_dump(exclude_unset=True)

        # Verify new department if provided
        if "department_id" in update_data:
            dept_stmt = select(Department).where(
                Department.id == update_data["department_id"]
            )
            dept_result = await db.execute(dept_stmt)
            if not dept_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
                )

        # Verify new position if provided
        if "position_id" in update_data:
            pos_stmt = select(Position).where(Position.id == update_data["position_id"])
            pos_result = await db.execute(pos_stmt)
            if not pos_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Position not found"
                )

        for field, value in update_data.items():
            setattr(employee, field, value)

        await db.commit()
        await db.refresh(employee)

        return employee

    @staticmethod
    async def terminate_employee(
        db: AsyncSession, employee_id: str, termination_date: date
    ) -> Employee:
        """Terminate an employee"""
        stmt = select(Employee).where(Employee.id == employee_id)
        result = await db.execute(stmt)
        employee = result.scalar_one_or_none()

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
            )

        employee.employment_status = "terminated"
        employee.termination_date = termination_date

        await db.commit()
        await db.refresh(employee)

        return employee

    #  Event driven
    @staticmethod
    async def create_employee_with_events(
        db: AsyncSession, employee_data: EmployeeCreate, rabbitmq: RabbitMQClient
    ) -> Employee:
        """Create employee and publish event"""
        employee = await EmployeeService.create_employee(db, employee_data)

        # Publish event
        await EventPublisher.publish_employee_created(rabbitmq, employee)

        return employee

    @staticmethod
    async def terminate_employee_with_events(
        db: AsyncSession,
        employee_id: str,
        termination_date: date,
        rabbitmq: RabbitMQClient,
        reason: Optional[str] = None,
    ) -> Employee:
        """Terminate employee and publish event"""
        employee = await EmployeeService.terminate_employee(
            db, employee_id, termination_date
        )

        # Publish event
        await EventPublisher.publish_employee_terminated(rabbitmq, employee, reason)

        return employee
