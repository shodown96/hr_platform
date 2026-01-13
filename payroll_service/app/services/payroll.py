from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from app.messaging.rabbitmq import RabbitMQClient
from fastapi import HTTPException, status
from schemas.payroll import (
    EmployeeSalaryCreate,
    PayrollRecordCreate,
    PayrollRecordUpdate,
    PayrollSummary,
)
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.payroll import (
    EmployeeSalary,
    PaymentStatus,
    PayrollRecord,
    SalaryComponent,
    SalaryComponentType,
)


class EmployeeSalaryService:

    @staticmethod
    async def create_employee_salary(
        db: AsyncSession, salary_data: EmployeeSalaryCreate
    ) -> EmployeeSalary:
        """Create salary record for employee"""
        # Check if employee already has active salary
        stmt = select(EmployeeSalary).where(
            and_(
                EmployeeSalary.employee_id == salary_data.employee_id,
                EmployeeSalary.is_active == True,
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Deactivate old salary
            existing.is_active = False
            existing.effective_to = salary_data.effective_from - timedelta(days=1)

        # Create new salary record
        salary = EmployeeSalary(**salary_data.model_dump())
        db.add(salary)
        await db.commit()
        await db.refresh(salary)

        return salary

    @staticmethod
    async def get_employee_salary(
        db: AsyncSession, employee_id: str, as_of_date: Optional[date] = None
    ) -> Optional[EmployeeSalary]:
        """Get current or historical salary for employee"""
        if as_of_date is None:
            as_of_date = date.today()

        stmt = select(EmployeeSalary).where(
            and_(
                EmployeeSalary.employee_id == employee_id,
                EmployeeSalary.effective_from <= as_of_date,
                (EmployeeSalary.effective_to.is_(None))
                | (EmployeeSalary.effective_to >= as_of_date),
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_salary_history(
        db: AsyncSession, employee_id: str
    ) -> List[EmployeeSalary]:
        """Get salary history for employee"""
        stmt = (
            select(EmployeeSalary)
            .where(EmployeeSalary.employee_id == employee_id)
            .order_by(EmployeeSalary.effective_from.desc())
        )

        result = await db.execute(stmt)
        return result.scalars().all()


class PayrollService:

    @staticmethod
    async def create_payroll_record(
        db: AsyncSession, payroll_data: PayrollRecordCreate
    ) -> PayrollRecord:
        """Create payroll record for an employee"""
        # Get employee's current salary
        salary = await EmployeeSalaryService.get_employee_salary(
            db, payroll_data.employee_id, payroll_data.pay_period_start
        )

        if not salary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No salary record found for employee {payroll_data.employee_id}",
            )

        # Check for existing payroll in this period
        stmt = select(PayrollRecord).where(
            and_(
                PayrollRecord.employee_id == payroll_data.employee_id,
                PayrollRecord.pay_period_start == payroll_data.pay_period_start,
                PayrollRecord.pay_period_end == payroll_data.pay_period_end,
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payroll record already exists for this period",
            )

        # Calculate gross salary based on frequency
        gross_salary = PayrollService._calculate_gross_salary(
            salary.basic_salary,
            salary.payment_frequency,
            payroll_data.pay_period_start,
            payroll_data.pay_period_end,
        )

        # Create payroll record
        payroll = PayrollRecord(
            employee_id=payroll_data.employee_id,
            employee_salary_id=str(salary.id),
            pay_period_start=payroll_data.pay_period_start,
            pay_period_end=payroll_data.pay_period_end,
            gross_salary=gross_salary,
            total_deductions=0,
            net_salary=gross_salary,
        )

        db.add(payroll)
        await db.flush()

        # Add components
        total_additions = Decimal(0)
        total_deductions = Decimal(0)

        # Add basic salary component
        basic_component = SalaryComponent(
            payroll_record_id=str(payroll.id),
            component_type=SalaryComponentType.BASIC,
            amount=gross_salary,
            description="Basic Salary",
        )
        db.add(basic_component)

        # Add additional components
        for component_data in payroll_data.components:
            component = SalaryComponent(
                payroll_record_id=str(payroll.id), **component_data.model_dump()
            )
            db.add(component)

            if component.component_type in [
                SalaryComponentType.DEDUCTION,
                SalaryComponentType.TAX,
            ]:
                total_deductions += Decimal(str(component.amount))
            else:
                total_additions += Decimal(str(component.amount))

        # Update payroll totals
        payroll.total_deductions = float(total_deductions)
        payroll.net_salary = float(
            Decimal(str(gross_salary)) + total_additions - total_deductions
        )

        await db.commit()
        await db.refresh(payroll)

        return payroll

    @staticmethod
    def _calculate_gross_salary(
        basic_salary: float, frequency: str, period_start: date, period_end: date
    ) -> float:
        """Calculate gross salary for pay period"""
        if frequency == "monthly":
            return basic_salary
        elif frequency == "bi_weekly":
            return basic_salary / 2
        elif frequency == "weekly":
            return basic_salary / 4
        elif frequency == "annual":
            return basic_salary / 12
        return basic_salary

    @staticmethod
    async def get_payroll_record(
        db: AsyncSession, payroll_id: str
    ) -> Optional[PayrollRecord]:
        """Get payroll record with components"""
        stmt = (
            select(PayrollRecord)
            .options(selectinload(PayrollRecord.salary_components))
            .where(PayrollRecord.id == payroll_id)
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_employee_payroll_records(
        db: AsyncSession,
        employee_id: str,
        year: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PayrollRecord]:
        """Get payroll records for employee"""
        stmt = select(PayrollRecord).where(PayrollRecord.employee_id == employee_id)

        if year:
            stmt = stmt.where(
                func.extract("year", PayrollRecord.pay_period_start) == year
            )

        stmt = (
            stmt.order_by(PayrollRecord.pay_period_start.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def update_payroll_record(
        db: AsyncSession, payroll_id: str, payroll_data: PayrollRecordUpdate
    ) -> PayrollRecord:
        """Update payroll record"""
        stmt = select(PayrollRecord).where(PayrollRecord.id == payroll_id)
        result = await db.execute(stmt)
        payroll = result.scalar_one_or_none()

        if not payroll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Payroll record not found"
            )

        update_data = payroll_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(payroll, field, value)

        await db.commit()
        await db.refresh(payroll)

        return payroll

    @staticmethod
    async def process_payment(
        db: AsyncSession,
        payroll_id: str,
        payment_method: str,
        payment_reference: str,
        rabbitmq: RabbitMQClient = None,
    ) -> PayrollRecord:
        """Mark payroll as paid and publish event"""
        payroll = await PayrollService.get_payroll_record(db, payroll_id)

        if not payroll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Payroll record not found"
            )

        if payroll.payment_status == PaymentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payroll already processed",
            )
            
        # TODO: Actually process payment through stripe/paystack

        payroll.payment_status = PaymentStatus.COMPLETED
        payroll.payment_date = date.today()
        payroll.payment_method = payment_method
        payroll.payment_reference = payment_reference

        await db.commit()
        await db.refresh(payroll)

        # Publish event
        if rabbitmq:
            from services.event_publisher import PayrollEventPublisher

            await PayrollEventPublisher.publish_payroll_processed(rabbitmq, payroll)

        return payroll

    @staticmethod
    async def get_payroll_summary(
        db: AsyncSession, start_date: date, end_date: date
    ) -> PayrollSummary:
        """Get payroll summary for period"""
        stmt = select(
            func.count(PayrollRecord.id).label("total_employees"),
            func.sum(PayrollRecord.gross_salary).label("total_gross"),
            func.sum(PayrollRecord.total_deductions).label("total_deductions"),
            func.sum(PayrollRecord.net_salary).label("total_net"),
            func.sum(
                func.case(
                    (PayrollRecord.payment_status == PaymentStatus.PENDING, 1), else_=0
                )
            ).label("pending_count"),
            func.sum(
                func.case(
                    (PayrollRecord.payment_status == PaymentStatus.COMPLETED, 1),
                    else_=0,
                )
            ).label("completed_count"),
        ).where(
            and_(
                PayrollRecord.pay_period_start >= start_date,
                PayrollRecord.pay_period_end <= end_date,
            )
        )

        result = await db.execute(stmt)
        row = result.first()

        return PayrollSummary(
            total_employees=row.total_employees or 0,
            total_gross_salary=float(row.total_gross or 0),
            total_deductions=float(row.total_deductions or 0),
            total_net_salary=float(row.total_net or 0),
            pending_count=row.pending_count or 0,
            completed_count=row.completed_count or 0,
        )
