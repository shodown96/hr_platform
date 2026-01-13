import aio_pika
import json
from sqlalchemy.ext.asyncio import AsyncSession


class EmployeeEventConsumer:
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None

    async def start(self):
        """Start consuming employee events"""
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()

        # Declare exchange
        exchange = await self.channel.declare_exchange(
            "employee_events", aio_pika.ExchangeType.TOPIC, durable=True
        )

        # Declare queue for auth service
        queue = await self.channel.declare_queue(
            "auth_service_employee_events", durable=True
        )

        # Bind to employee events
        await queue.bind(exchange, routing_key="employee.*")

        # Start consuming
        await queue.consume(self.process_message)

    # TODO; is this necessary
    async def stop(self):
        if self.channel and self.consumer_tag:
            await self.channel.cancel(self.consumer_tag)

        if self.channel:
            await self.channel.close()

        if self.connection:
            await self.connection.close()

    async def process_message(self, message: aio_pika.IncomingMessage):
        """Process incoming employee event"""
        async with message.process():
            event_data = json.loads(message.body.decode())

            event_type = event_data.get("event_type")

            if event_type == "employee.terminated":
                await self.handle_employee_terminated(event_data)
            elif event_type == "employee.updated":
                await self.handle_employee_updated(event_data)

    async def handle_employee_terminated(self, event_data: dict):
        """Handle employee termination - deactivate user account"""
        from sqlalchemy import select, update
        from app.models.auth import User

        user_id = event_data["user_id"]

        async with AsyncSession() as db:
            # Find user by user_id
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                # Deactivate user account
                user.is_active = False
                await db.commit()
                print(f"Deactivated user account for employee with user_id: {user_id}")

    async def handle_employee_updated(self, event_data: dict):
        """Handle employee updates - sync email changes"""
        from sqlalchemy import select
        from models.auth import User

        user_id = event_data["user_id"]
        updated_fields = event_data.get("updated_fields", {})

        if "email" in updated_fields:
            async with AsyncSession() as db:
                stmt = select(User).where(User.id == user_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    user.email = event_data["employee_email"]
                    await db.commit()
                    print(f"Updated email for user {user.id}")
