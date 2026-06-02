from datetime import datetime, UTC
from typing import Optional
from uuid import uuid4

from app.messaging.rabbitmq import RabbitMQClient
from app.models.employee import Department, Employee, Position
from app.schemas.events import (
    EmployeeCreatedEvent,
    EmployeeTerminatedEvent,
    EmployeeUpdatedEvent,
)


class EventPublisher:

    @staticmethod
    async def publish_employee_created(
        rabbitmq: RabbitMQClient,
        employee: Employee,
    ) -> None:
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
            department_id=str(employee.department_id) if employee.department_id else None,
            position_id=str(employee.position_id) if employee.position_id else None,
        )
        await rabbitmq.publish_event(
            routing_key="employee.created",
            event_data=event.model_dump(mode="json"),
        )

    @staticmethod
    async def publish_employee_updated(
        rabbitmq: RabbitMQClient,
        employee: Employee,
        updated_fields: dict,
    ) -> None:
        event = EmployeeUpdatedEvent(
            event_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            user_id=str(employee.user_id),
            employee_id=str(employee.id),
            employee_code=employee.employee_code,
            employee_email=employee.email,
            updated_fields=updated_fields,
        )
        await rabbitmq.publish_event(
            routing_key="employee.updated",
            event_data=event.model_dump(mode="json"),
        )

    @staticmethod
    async def publish_employee_terminated(
        rabbitmq: RabbitMQClient,
        employee: Employee,
        reason: Optional[str] = None,
    ) -> None:
        event = EmployeeTerminatedEvent(
            event_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            user_id=str(employee.user_id),
            employee_id=str(employee.id),
            employee_code=employee.employee_code,
            employee_email=employee.email,
            termination_date=(
                employee.termination_date.isoformat()
                if employee.termination_date
                else None
            ),
            reason=reason,
        )
        await rabbitmq.publish_event(
            routing_key="employee.terminated",
            event_data=event.model_dump(mode="json"),
        )

    @staticmethod
    async def publish_employee_department_changed(
        rabbitmq: RabbitMQClient,
        employee: Employee,
        department: Department,
    ) -> None:
        event = {
            "event_id": str(uuid4()),
            "event_type": "employee.department.changed",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": str(employee.user_id),
            "employee_id": str(employee.id),
            "employee_code": employee.employee_code,
            "employee_email": employee.email,
            "department_id": str(department.id),
            "department_name": department.name,
            "effective_date": datetime.now(UTC).date().isoformat(),
        }
        await rabbitmq.publish_event(
            routing_key="employee.department.changed",
            event_data=event,
        )

    @staticmethod
    async def publish_employee_position_changed(
        rabbitmq: RabbitMQClient,
        employee: Employee,
        position: Position,
    ) -> None:
        event = {
            "event_id": str(uuid4()),
            "event_type": "employee.position.changed",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": str(employee.user_id),
            "employee_id": str(employee.id),
            "employee_code": employee.employee_code,
            "employee_email": employee.email,
            "position_id": str(position.id),
            "position_name": position.name,
            "effective_date": datetime.now(UTC).date().isoformat(),
        }
        await rabbitmq.publish_event(
            routing_key="employee.position.changed",
            event_data=event,
        )
