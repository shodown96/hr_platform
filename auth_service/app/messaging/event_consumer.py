# auth_service/app/messaging/event_consumer.py
import json

import aio_pika
from app.core.db import AsyncSession
from app.models.auth import User
from sqlalchemy import select


class EmployeeEventConsumer:
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None

    async def start(self):
        """Start consuming employee events"""
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()

        exchange = await self.channel.declare_exchange(
            "employee_events", aio_pika.ExchangeType.TOPIC, durable=True
        )

        queue = await self.channel.declare_queue(
            "auth_service_employee_events", durable=True
        )

        await queue.bind(exchange, routing_key="employee.*")

        await queue.consume(self.process_message)
        print("✅ Auth Service: Listening for employee events")

    async def process_message(self, message: aio_pika.IncomingMessage):
        """Process incoming employee event"""
        async with message.process():
            try:
                event_data = json.loads(message.body.decode())
                event_type = event_data.get("event_type")

                if event_type == "employee.terminated":
                    await self.handle_employee_terminated(event_data)
                elif event_type == "employee.updated":
                    await self.handle_employee_updated(event_data)
            except Exception as e:
                print(f"❌ Error processing employee event: {e}")

    async def handle_employee_terminated(self, event_data: dict):
        """Handle employee termination - deactivate user account"""
        user_id = event_data["user_id"]

        async with AsyncSession() as db:
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                user.is_active = False
                await db.commit()
                print(f"✅ Deactivated user account for user_id: {user_id}")

    async def handle_employee_updated(self, event_data: dict):
        """Handle employee updates - sync email changes"""
        user_id = event_data["user_id"]
        updated_fields = event_data.get("updated_fields", {})

        if "email" in updated_fields:
            async with AsyncSession() as db:
                stmt = select(User).where(User.id == user_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    user.email = event_data["email"]
                    await db.commit()
                    print(f"✅ Updated email for user {user.id}")
