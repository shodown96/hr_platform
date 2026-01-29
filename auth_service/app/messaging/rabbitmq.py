# auth_service/app/messaging/rabbitmq.py
import json
from datetime import datetime
from typing import Annotated, Any, Dict
from uuid import uuid4

import aio_pika
from fastapi import Depends


class RabbitMQClient:
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()

        self.exchange = await self.channel.declare_exchange(
            "auth_events",
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

    async def close(self):
        """Close connection"""
        if self.connection:
            await self.connection.close()

    async def publish_event(self, routing_key: str, event_data: Dict[str, Any]):
        """Publish an event to the exchange"""
        if not self.channel:
            await self.connect()

        message = aio_pika.Message(
            body=json.dumps(event_data).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await self.exchange.publish(message, routing_key=routing_key)


# Global RabbitMQ client instance
rabbitmq_client = None


async def get_rabbitmq_client() -> RabbitMQClient:
    """Dependency to get RabbitMQ client"""
    global rabbitmq_client
    if rabbitmq_client is None:
        from app.core.config import settings

        rabbitmq_client = RabbitMQClient(settings.RABBITMQ_URL)
        await rabbitmq_client.connect()
    return rabbitmq_client


RabbitMQDep = Annotated[RabbitMQClient, Depends(get_rabbitmq_client)]
