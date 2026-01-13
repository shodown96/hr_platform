# from api import api_router
# from app.core.setup import create_application
# from app.core.config import settings

# app = create_application(router=api_router, settings=settings)


import asyncio
from collections.abc import AsyncGenerator, Callable
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from typing import Any

import anyio
import redis.asyncio as redis
from app.api import api_router
from app.core.config import (
    AppSettings,
    ClientSideCacheSettings,
    CORSSettings,
    DatabaseSettings,
    EnvironmentSettings,
    RabbitMQSettings,
    RedisCacheSettings,
    RedisQueueSettings,
    settings,
)
from app.core.db import Base, SessionDep
from app.core.db import async_engine as engine
from app.core.health import check_database_health, check_redis_health
from app.core.utils import cache, queue
from app.messaging.event_consumer import EmployeeEventConsumer
from app.models import *  # noqa: F403
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# -------------- database --------------
async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# -------------- cache --------------
async def create_redis_cache_pool() -> None:
    cache.pool = redis.ConnectionPool.from_url(settings.REDIS_CACHE_URL)
    cache.client = redis.Redis.from_pool(cache.pool)  # type: ignore


async def close_redis_cache_pool() -> None:
    if cache.client is not None:
        await cache.client.aclose()  # type: ignore


# -------------- queue --------------
async def create_redis_queue_pool() -> None:
    queue.pool = await create_pool(
        RedisSettings(host=settings.REDIS_QUEUE_HOST, port=settings.REDIS_QUEUE_PORT)
    )


async def close_redis_queue_pool() -> None:
    if queue.pool is not None:
        await queue.pool.aclose()  # type: ignore


# -------------- application --------------
async def set_threadpool_tokens(number_of_tokens: int = 100) -> None:
    limiter = anyio.to_thread.current_default_thread_limiter()
    limiter.total_tokens = number_of_tokens


# -------------- consumer --------------
async def start_event_consumer():
    """Start event consumer on app startup"""
    consumer = EmployeeEventConsumer(settings.RABBITMQ_URL)
    asyncio.create_task(consumer.start())


app = FastAPI(
    title="HR Auth Service",
    description="Authentication and Authorization Microservice",
    version="1.0.0",
)


def lifespan_factory(
    settings: (
        DatabaseSettings
        | RedisCacheSettings
        | AppSettings
        | ClientSideCacheSettings
        | CORSSettings
        | RedisQueueSettings
        | EnvironmentSettings
        | RabbitMQSettings
    ),
    create_tables_on_start: bool = True,
) -> Callable[[FastAPI], _AsyncGeneratorContextManager[Any]]:
    """Factory to create a lifespan async context manager for a FastAPI app."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator:
        from asyncio import Event

        initialization_complete = Event()
        app.state.initialization_complete = initialization_complete

        await set_threadpool_tokens()

        try:
            if isinstance(settings, RedisCacheSettings):
                await create_redis_cache_pool()

            if isinstance(settings, RedisQueueSettings):
                await create_redis_queue_pool()

            if create_tables_on_start:
                await create_tables()

            if isinstance(settings, RabbitMQSettings):
                await start_event_consumer()

            initialization_complete.set()

            yield

        finally:
            if isinstance(settings, RedisCacheSettings):
                await close_redis_cache_pool()

            if isinstance(settings, RedisQueueSettings):
                await close_redis_queue_pool()

    return lifespan


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Include routers
app.include_router(api_router)


@app.get("/", tags=["Base"])
async def get_base_endpoint(db: SessionDep, redis: cache.RedisDep):
    db_health = await check_database_health(db)
    redis_health = await check_redis_health(redis)
    return {
        "message": "Welcome to HR Platform API | Auth Service",
        "health": {
            "database": f"{'un'if not db_health else ''}healthy",
            "redis": f"{'un'if not redis_health else ''}healthy",
        },
    }
