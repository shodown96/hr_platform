from typing import Optional
from uuid import uuid4
from datetime import datetime, UTC
from app.models.employment import Employee
from app.messaging.rabbitmq import RabbitMQClient
from app.schemas.events import (
    EmployeeCreatedEvent,
    EmployeeUpdatedEvent,
    EmployeeTerminatedEvent
)


class EventPublisher:
    
    @staticmethod
    async def publish_employee_created(
        rabbitmq: RabbitMQClient,
        employee: Employee
    ):
        """Publish employee created event"""
        event = EmployeeCreatedEvent(
            event_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            user_id=str(employee.user_id),
            employee_id=str(employee.id),
            employee_code=employee.employee_code,
            employee_email=employee.email,
            first_name=employee.first_name,
            last_name=employee.last_name,
            hire_date=employee.hire_date.isoformat(),
            department_id=str(employee.department_id),
            position_id=str(employee.position_id)
        )
        
        await rabbitmq.publish_event(
            routing_key="employee.created",
            event_data=event.model_dump()
        )
    
    @staticmethod
    async def publish_employee_updated(
        rabbitmq: RabbitMQClient,
        employee: Employee,
        updated_fields: dict
    ):
        """Publish employee updated event"""
        event = EmployeeUpdatedEvent(
            event_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            employee_id=str(employee.id),
            employee_code=employee.employee_code,
            employee_email=employee.email,
            updated_fields=updated_fields
        )
        
        await rabbitmq.publish_event(
            routing_key="employee.updated",
            event_data=event.model_dump()
        )
    
    @staticmethod
    async def publish_employee_terminated(
        rabbitmq: RabbitMQClient,
        employee: Employee,
        reason: Optional[str] = None
    ):
        """Publish employee terminated event"""
        event = EmployeeTerminatedEvent(
            event_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            employee_id=str(employee.id),
            employee_code=employee.employee_code,
            employee_email=employee.email,
            termination_date=employee.termination_date.isoformat(),
            reason=reason
        )
        
        await rabbitmq.publish_event(
            routing_key="employee.terminated",
            event_data=event.model_dump()
        )
