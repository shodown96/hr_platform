from typing import List, Optional

from fastapi import HTTPException, status
from app.schemas.employment import PositionCreate, PositionUpdate
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employment import Department, Position


class PositionService:

    @staticmethod
    async def create_position(
        db: AsyncSession, position_data: PositionCreate
    ) -> Position:
        """Create a new position"""
        # Check if department exists
        # TEST
        # await db.execute(delete(Position))
        # await db.commit()
        dept_stmt = select(Department).where(
            Department.id == position_data.department_id
        )
        dept_result = await db.execute(dept_stmt)
        if not dept_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
            )

        position = Position(**position_data.model_dump())
        db.add(position)
        await db.commit()
        await db.refresh(position)

        return position

    @staticmethod
    async def get_position(db: AsyncSession, position_id: str) -> Optional[Position]:
        """Get position by ID"""
        stmt = select(Position).where(Position.id == position_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_positions(
        db: AsyncSession,
        department_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Position]:
        """Get positions with optional department filter"""
        stmt = select(Position)

        if department_id:
            stmt = stmt.where(Position.department_id == department_id)

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
