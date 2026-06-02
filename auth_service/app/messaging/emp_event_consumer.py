# auth_service/app/messaging/event_consumer.py
import json

import aio_pika
from app.core.db import local_session
from app.models.auth import User
from sqlalchemy import select
from datetime import datetime, date
from app.core.shared.cache.permissions import get_permission_cache


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

                print(f"📩 Received employee event: {event_type}")

                if event_type == "employee.created":
                    await self.handle_employee_created(event_data)
                elif event_type == "employee.updated":
                    await self.handle_employee_updated(event_data)
                elif event_type == "employee.terminated":
                    await self.handle_employee_terminated(event_data)
                elif event_type == "employee.position.changed":
                    await self.handle_employee_position_changed(event_data)
                elif event_type == "employee.department.changed":
                    await self.handle_employee_department_changed(event_data)
                    
            except Exception as e:
                print(f"❌ Error processing employee event: {e}")

    async def handle_employee_created(self, event_data: dict):
        """
        Handle employee creation
        Auth Service: Nothing to do (user already created via invitation)
        """
        employee_id = event_data["employee_id"]
        user_id = event_data.get("user_id")
        
        print(f"ℹ️  Employee created: {employee_id}")
        print(f"   User ID: {user_id}")
        print(f"   No action needed - user account already exists")

    async def handle_employee_updated(self, event_data: dict):
        """
        Handle employee updates
        Auth Service: Sync email if changed
        """
        user_id = event_data["user_id"]
        updated_fields = event_data.get("updated_fields", {})

        if "email" in updated_fields:
            new_email = event_data.get("email")
            
            async with local_session() as db:
                stmt = select(User).where(User.id == user_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    old_email = user.email
                    user.email = new_email
                    await db.commit()
                    print(f"✅ Updated email for user {user.id}")
                    print(f"   Old: {old_email} → New: {new_email}")
                else:
                    print(f"⚠️  User {user_id} not found")

    async def handle_employee_terminated(self, event_data: dict):
        """
        Handle employee termination
        Auth Service: Deactivate user account
        """
        user_id = event_data["user_id"]
        employee_id = event_data["employee_id"]
        termination_date = event_data.get("termination_date")
        reason = event_data.get("reason")
        
        async with local_session() as db:
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                user.is_active = False
                await db.commit()
                print(f"✅ Deactivated user account for employee {employee_id}")
                print(f"   User ID: {user_id}")
                print(f"   Termination Date: {termination_date}")
                print(f"   Reason: {reason}")
            else:
                print(f"⚠️  User {user_id} not found for employee {employee_id}")

    async def handle_employee_position_changed(self, event_data: dict):
        """
        Handle employee position change
        Auth Service: Clear permission cache (permissions may change)
        """
        
        employee_id = event_data["employee_id"]
        user_id = event_data.get("user_id")
        old_position_id = event_data.get("old_position_id")
        new_position_id = event_data.get("new_position_id")
        effective_date_str = event_data.get("effective_date")
        
        print(f"🔄 Position changed for employee {employee_id}")
        print(f"   Old Position: {old_position_id}")
        print(f"   New Position: {new_position_id}")
        print(f"   Effective Date: {effective_date_str}")
        
        # Parse effective date
        effective_date = date.fromisoformat(effective_date_str) if effective_date_str else date.today()
        
        # Only invalidate cache if change is effective now or in the past
        if effective_date <= date.today():
            if user_id:
                cache = await get_permission_cache()
                await cache.invalidate_all_for_user(user_id)
                print(f"✅ Cache invalidated for user {user_id}")
                print(f"   User will get fresh permissions on next request")
            else:
                print(f"⚠️  No user_id provided, cannot invalidate cache")
        else:
            print(f"ℹ️  Change effective in future ({effective_date})")
            print(f"   Cache will be cleared when effective date arrives")


    async def handle_employee_department_changed(self, event_data: dict):
        """
        Handle employee department change
        Auth Service: Clear permission cache (permissions may change)
        """
        
        employee_id = event_data["employee_id"]
        user_id = event_data.get("user_id")
        old_department_id = event_data.get("old_department_id")
        new_department_id = event_data.get("new_department_id")
        effective_date_str = event_data.get("effective_date")
        
        print(f"🔄 Department changed for employee {employee_id}")
        print(f"   Old Department: {old_department_id}")
        print(f"   New Department: {new_department_id}")
        print(f"   Effective Date: {effective_date_str}")
        
        # Parse effective date
        effective_date = date.fromisoformat(effective_date_str) if effective_date_str else date.today()
        
        # Only invalidate cache if change is effective now or in the past
        if effective_date <= date.today():
            if user_id:
                cache = await get_permission_cache()
                await cache.invalidate_all_for_user(user_id)
                print(f"✅ Cache invalidated for user {user_id}")
                print(f"   User will get fresh permissions on next request")
            else:
                print(f"⚠️  No user_id provided, cannot invalidate cache")
        else:
            print(f"ℹ️  Change effective in future ({effective_date})")
            print(f"   Cache will be cleared when effective date arrives")
