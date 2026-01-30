from uuid import uuid4
from typing import List
from datetime import datetime, UTC
from app.messaging.rabbitmq import RabbitMQClient


class AuthEventPublisher:
    """Publish auth-related events"""
    
    # Not to be used, permissions should be reset instead
    @staticmethod
    async def publish_permissions_changed(
        rabbitmq: RabbitMQClient,
        user_id: str,
        old_permissions: List[str] = [],
        new_permissions: List[str] = []
    ):
        """
        Publish when user's permissions change
        All services listen and invalidate their caches
        """
        event = {
            "event_id": str(uuid4()),
            "event_type": "user.permissions.changed",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id,
            "old_permissions": old_permissions,
            "new_permissions": new_permissions,
            "added_permissions": list(set(new_permissions) - set(old_permissions)),
            "removed_permissions": list(set(old_permissions) - set(new_permissions))
        }
        
        await rabbitmq.publish_event(
            routing_key="user.permissions.changed",
            event_data=event
        )
        print(f"📤 Published permissions changed for user {user_id}")
    
    @staticmethod
    async def publish_role_assigned(
        rabbitmq: RabbitMQClient,
        user_id: str,
        role_id: str,
        role_name: str
    ):
        """Publish when role is assigned to user"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "user.role.assigned",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id,
            "role_id": role_id,
            "role_name": role_name
        }
        print("Publishing event")
        await rabbitmq.publish_event(
            routing_key="user.role.assigned",
            event_data=event
        )
    
    @staticmethod
    async def publish_role_removed(
        rabbitmq: RabbitMQClient,
        user_id: str,
        role_id: str,
        role_name: str
    ):
        """Publish when role is removed from user"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "user.role.removed",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id,
            "role_id": role_id,
            "role_name": role_name
        }
        
        await rabbitmq.publish_event(
            routing_key="user.role.removed",
            event_data=event
        )
        
    @staticmethod
    async def publish_permission_granted(
        rabbitmq: RabbitMQClient,
        user_id: str,
        permission_id: str,
        permission_name: str
    ):
        """Publish when permission is granted to user"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "user.permission.granted",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id,
            "permission_id": permission_id,
            "permission_name": permission_name
        }
        print("Publishing event")
        await rabbitmq.publish_event(
            routing_key="user.permission.granted",
            event_data=event
        )

    
    @staticmethod
    async def publish_permission_removed(
        rabbitmq: RabbitMQClient,
        user_id: str,
        permission_id: str,
        permission_name: str
    ):
        """Publish when a permission is removed from user"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "user.permission.removed",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id,
            "permission_id": permission_id,
            "permission_name": permission_name
        }
        
        await rabbitmq.publish_event(
            routing_key="user.role.removed",
            event_data=event
        )
           
    
    @staticmethod
    async def publish_user_deactivated(
        rabbitmq: RabbitMQClient,
        user_id: str
    ):
        """Publish when user is deactivated"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "user.deactivated",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id
        }
        
        await rabbitmq.publish_event(
            routing_key="user.deactivated",
            event_data=event
        )
            
    @staticmethod
    async def publish_user_password_changed(
        rabbitmq: RabbitMQClient,
        user_id: str
    ):
        """Publish when user changes their password"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "user.password.changed",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id
        }
        
        await rabbitmq.publish_event(
            routing_key="user.password.changed",
            event_data=event
        )

            
    @staticmethod
    async def publish_user_password_reset(
        rabbitmq: RabbitMQClient,
        user_id: str
    ):
        """Publish when user resets their password"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "user.password.reset",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id
        }
        
        await rabbitmq.publish_event(
            routing_key="user.password.reset",
            event_data=event
        )
