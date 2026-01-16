import json

import aio_pika
from shared.cache.permissions import get_permission_cache
from app.core.config import settings

class AuthEventConsumer:
    """
    Listen to auth events in Employee/Payroll services
    Invalidate cache when permissions change
    """

    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None

    async def start(self):
        """Start consuming auth events"""
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()

        # Declare exchange
        exchange = await self.channel.declare_exchange(
            "auth_events", aio_pika.ExchangeType.TOPIC, durable=True
        )

        # Declare queue (unique per service)
        queue = await self.channel.declare_queue(
            f"{settings.SERVICE_NAME}_auth_events",  # e.g., "employee_service_auth_events"
            durable=True,
        )

        # Bind to permission/role events
        await queue.bind(exchange, routing_key="user.permissions.#")
        await queue.bind(exchange, routing_key="user.role.#")
        await queue.bind(exchange, routing_key="user.deactivated")

        # Start consuming
        await queue.consume(self.process_message)
        print(f"✅ {settings.SERVICE_NAME}: Listening for auth events")

    async def process_message(self, message: aio_pika.IncomingMessage):
        """Process auth event"""
        async with message.process():
            try:
                event_data = json.loads(message.body.decode())
                event_type = event_data.get("event_type")

                print(f"📩 Received auth event: {event_type}")

                if event_type == "user.permissions.changed":
                    await self.handle_permissions_changed(event_data)
                elif event_type in ["user.role.assigned", "user.role.removed"]:
                    await self.handle_role_changed(event_data)
                elif event_type == "user.deactivated":
                    await self.handle_user_deactivated(event_data)

            except Exception as e:
                print(f"❌ Error processing auth event: {e}")

    async def handle_permissions_changed(self, event_data: dict):
        """Handle permission change - invalidate cache"""
        user_id = event_data["user_id"]

        print(f"🔄 Permissions changed for user {user_id}")
        print(f"   Removed: {event_data.get('removed_permissions', [])}")
        print(f"   Added: {event_data.get('added_permissions', [])}")

        # Invalidate cache - user will get fresh permissions on next request
        cache = await get_permission_cache()
        await cache.invalidate_all_for_user(user_id)

        print(f"✅ Cache invalidated for user {user_id}")

    async def handle_role_changed(self, event_data: dict):
        """Handle role assignment/removal - invalidate cache"""
        user_id = event_data["user_id"]
        role_name = event_data["role_name"]

        print(f"🔄 Role '{role_name}' changed for user {user_id}")

        # Invalidate cache
        cache = await get_permission_cache()
        await cache.invalidate_all_for_user(user_id)

        print(f"✅ Cache invalidated for user {user_id}")

    async def handle_user_deactivated(self, event_data: dict):
        """Handle user deactivation - invalidate everything"""
        user_id = event_data["user_id"]

        print(f"🚫 User {user_id} deactivated")

        # Invalidate cache
        cache = await get_permission_cache()
        await cache.invalidate_all_for_user(user_id)

        print(f"✅ All cache cleared for user {user_id}")
