import json
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import aio_pika
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import local_session
from app.models.payroll import (
    EmployeeSalary,
    PaymentFrequency,
    PaymentStatus,
    PayrollRecord,
)


class EmployeeEventConsumer:
    """Listen to Employee Service events and react to salary lifecycle changes."""

    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None

    async def start(self) -> None:
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()

        exchange = await self.channel.declare_exchange(
            "employee_events",
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        queue = await self.channel.declare_queue(
            f"{settings.SERVICE_NAME}_employee_events",
            durable=True,
        )

        await queue.bind(exchange, routing_key="employee.#")
        await queue.consume(self.process_message)

        print(f"💰 {settings.SERVICE_NAME}: Listening for employee events")

    async def process_message(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process():
            try:
                routing_key = message.routing_key
                event_data: dict[str, Any] = json.loads(message.body.decode())

                print(f"📩 Payroll received: {routing_key}")

                if routing_key == "employee.created":
                    await self.handle_employee_created(event_data)
                elif routing_key == "employee.terminated":
                    await self.handle_employee_terminated(event_data)
                elif routing_key == "employee.position.changed":
                    await self.handle_employee_position_changed(event_data)
                elif routing_key == "employee.department.changed":
                    await self.handle_employee_department_changed(event_data)
                elif routing_key == "employee.updated":
                    await self.handle_employee_updated(event_data)

            except Exception as e:
                print(f"❌ Payroll event error: {e}")

    async def handle_employee_created(self, event_data: dict[str, Any]) -> None:
        employee_id = event_data["employee_id"]
        hire_date = date.fromisoformat(event_data["hire_date"])

        async with local_session() as db:
            result = await db.execute(
                select(EmployeeSalary).where(
                    EmployeeSalary.employee_id == employee_id,
                    EmployeeSalary.is_active == True,  # noqa: E712
                )
            )
            if result.scalar_one_or_none():
                return

            salary = EmployeeSalary(
                employee_id=employee_id,
                basic_salary=Decimal("0.00"),
                payment_frequency=PaymentFrequency.MONTHLY,
                effective_from=hire_date,
                currency="USD",
                is_active=True,
            )
            db.add(salary)
            await db.commit()

        print(f"✅ Salary placeholder created for {employee_id}")

    async def handle_employee_position_changed(self, event_data: dict[str, Any]) -> None:
        employee_id = event_data["employee_id"]
        effective_date = date.fromisoformat(event_data["effective_date"])

        if effective_date <= date.today():
            async with local_session() as db:
                await self._version_salary(db, employee_id, effective_date)
            print(f"📈 Salary versioned due to position change for {employee_id}")

    async def handle_employee_department_changed(self, event_data: dict[str, Any]) -> None:
        employee_id = event_data["employee_id"]
        effective_date = date.fromisoformat(event_data["effective_date"])

        if effective_date <= date.today():
            async with local_session() as db:
                await self._version_salary(db, employee_id, effective_date)
            print(f"🔄 Salary versioned due to department change for {employee_id}")

    async def handle_employee_updated(self, event_data: dict[str, Any]) -> None:
        employee_id = event_data["employee_id"]
        updated_fields = event_data.get("updated_fields", {})

        if "department_id" in updated_fields or "position_id" in updated_fields:
            print(f"🔍 Salary review required for {employee_id}")

    async def handle_employee_terminated(self, event_data: dict[str, Any]) -> None:
        employee_id = event_data["employee_id"]
        termination_date = date.fromisoformat(event_data["termination_date"])

        async with local_session() as db:
            result = await db.execute(
                select(EmployeeSalary).where(
                    EmployeeSalary.employee_id == employee_id,
                    EmployeeSalary.is_active == True,  # noqa: E712
                )
            )
            salary = result.scalar_one_or_none()

            if not salary:
                return

            salary.is_active = False
            salary.effective_to = termination_date

            days_in_month = Decimal("30")
            days_worked = Decimal(str(termination_date.day))
            gross = (Decimal(str(salary.basic_salary)) / days_in_month) * days_worked

            payroll_record = PayrollRecord(
                employee_id=employee_id,
                employee_salary_id=str(salary.id),
                pay_period_start=date(termination_date.year, termination_date.month, 1),
                pay_period_end=termination_date,
                gross_salary=float(gross),
                net_salary=float(gross),
            )

            db.add(payroll_record)
            await db.commit()

        print(f"💵 Final payroll record created for {employee_id}")

    async def _version_salary(
        self, db: AsyncSession, employee_id: str, effective_date: date
    ) -> None:
        result = await db.execute(
            select(EmployeeSalary).where(
                EmployeeSalary.employee_id == employee_id,
                EmployeeSalary.is_active == True,  # noqa: E712
            )
        )
        current_salary = result.scalar_one_or_none()

        if not current_salary:
            return

        current_salary.is_active = False
        current_salary.effective_to = effective_date - timedelta(days=1)

        new_salary = EmployeeSalary(
            employee_id=employee_id,
            basic_salary=current_salary.basic_salary,
            payment_frequency=current_salary.payment_frequency,
            effective_from=effective_date,
            currency=current_salary.currency,
            is_active=True,
        )

        db.add(new_salary)
        await db.commit()
