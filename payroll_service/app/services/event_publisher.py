from uuid import uuid4
from datetime import datetime, date
from app.messaging.rabbitmq import RabbitMQClient


class PayrollEventPublisher:
    """
    Publishes payroll events that other services might care about
    """
    
    @staticmethod
    async def publish_payroll_processed(
        rabbitmq: RabbitMQClient,
        payroll_record
    ):
        """
        Publish event when payroll is successfully processed
        Other services might need this (e.g., Finance Service, Accounting)
        """
        event = {
            "event_id": str(uuid4()),
            "event_type": "payroll.processed",
            "timestamp": datetime.utcnow().isoformat(),
            "employee_id": payroll_record.employee_id,
            "payroll_id": str(payroll_record.id),
            "pay_period_start": payroll_record.pay_period_start.isoformat(),
            "pay_period_end": payroll_record.pay_period_end.isoformat(),
            "gross_salary": float(payroll_record.gross_salary),
            "net_salary": float(payroll_record.net_salary),
            "payment_date": payroll_record.payment_date.isoformat() if payroll_record.payment_date else None,
            "payment_method": payroll_record.payment_method
        }
        
        await rabbitmq.publish_event(
            routing_key="payroll.processed",
            event_data=event
        )
        print(f"📤 Published payroll.processed event for employee {payroll_record.employee_id}")
    
    @staticmethod
    async def publish_salary_changed(
        rabbitmq: RabbitMQClient,
        employee_id: str,
        old_salary: float,
        new_salary: float,
        effective_from: date
    ):
        """
        Publish event when employee salary changes
        HR/Finance might need this for budgeting
        """
        event = {
            "event_id": str(uuid4()),
            "event_type": "salary.changed",
            "timestamp": datetime.utcnow().isoformat(),
            "employee_id": employee_id,
            "old_salary": float(old_salary),
            "new_salary": float(new_salary),
            "effective_from": effective_from.isoformat(),
            "change_percentage": ((new_salary - old_salary) / old_salary * 100) if old_salary > 0 else 0
        }
        
        await rabbitmq.publish_event(
            routing_key="salary.changed",
            event_data=event
        )
        print(f"📤 Published salary.changed event for employee {employee_id}")
