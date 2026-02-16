from uuid import uuid4
from datetime import datetime, date, UTC
from typing import Optional
from app.messaging.rabbitmq import RabbitMQClient


class PayrollEventPublisher:
    """
    Publishes payroll events that other services might care about
    """

    @staticmethod
    async def publish_payroll_processed(rabbitmq: RabbitMQClient, payroll_record):
        """
        Publish event when payroll is successfully processed
        Other services might need this (e.g., Finance Service, Accounting)
        """
        event = {
            "event_id": str(uuid4()),
            "event_type": "payroll.processed",
            "timestamp": datetime.now(UTC).isoformat(),
            "employee_id": payroll_record.employee_id,
            "payroll_id": str(payroll_record.id),
            "pay_period_start": payroll_record.pay_period_start.isoformat(),
            "pay_period_end": payroll_record.pay_period_end.isoformat(),
            "gross_salary": float(payroll_record.gross_salary),
            "net_salary": float(payroll_record.net_salary),
            "payment_date": (
                payroll_record.payment_date.isoformat()
                if payroll_record.payment_date
                else None
            ),
            "payment_method": payroll_record.payment_method,
        }

        await rabbitmq.publish_event(routing_key="payroll.processed", event_data=event)
        print(
            f"📤 Published payroll.processed event for employee {payroll_record.employee_id}"
        )

    @staticmethod
    async def publish_salary_created(
        rabbitmq: RabbitMQClient,
        employee_id: str,
        basic_salary: float,
        currency: str,
        payment_frequency: str,
        effective_from: date,
    ):
        """
        Publish event when salary is set for employee
        Finance/Reporting services need this for budget tracking
        """
        event = {
            "event_id": str(uuid4()),
            "event_type": "salary.created",
            "timestamp": datetime.now(UTC).isoformat(),
            "employee_id": employee_id,
            "basic_salary": float(basic_salary),
            "currency": currency,
            "payment_frequency": payment_frequency,
            "effective_from": effective_from.isoformat(),
        }

        await rabbitmq.publish_event(routing_key="salary.created", event_data=event)
        print(f"📤 Published salary.created event for employee {employee_id}")

    @staticmethod
    async def publish_salary_changed(
        rabbitmq: RabbitMQClient,
        employee_id: str,
        old_salary: float,
        new_salary: float,
        effective_from: date,
        approved_by: Optional[str] = None,
    ):
        """
        Publish event when employee salary changes
        Finance/Audit services need this for budgeting and compliance
        """
        change_percentage = (
            ((new_salary - old_salary) / old_salary * 100) if old_salary > 0 else 0
        )

        event = {
            "event_id": str(uuid4()),
            "event_type": "salary.changed",
            "timestamp": datetime.now(UTC).isoformat(),
            "employee_id": employee_id,
            "old_salary": float(old_salary),
            "new_salary": float(new_salary),
            "change_percentage": float(change_percentage),
            "effective_from": effective_from.isoformat(),
            "approved_by": approved_by,
        }

        await rabbitmq.publish_event(routing_key="salary.changed", event_data=event)
        print(f"📤 Published salary.changed event for employee {employee_id}")

    @staticmethod
    async def publish_payroll_failed(
        rabbitmq: RabbitMQClient, payroll_id: str, employee_id: str, error_reason: str
    ):
        """
        Publish event when payroll processing fails
        Notification service alerts HR/Finance
        """
        event = {
            "event_id": str(uuid4()),
            "event_type": "payroll.failed",
            "timestamp": datetime.now(UTC).isoformat(),
            "payroll_id": payroll_id,
            "employee_id": employee_id,
            "error_reason": error_reason,
        }

        await rabbitmq.publish_event(routing_key="payroll.failed", event_data=event)
        print(f"📤 Published payroll.failed event for employee {employee_id}")
