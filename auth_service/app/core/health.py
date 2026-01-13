import logging

from app.core.db import SessionDep
from redis.asyncio import Redis
from sqlalchemy import text

LOGGER = logging.getLogger(__name__)


async def check_database_health(db: SessionDep) -> bool:
    try:
        await db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        LOGGER.exception(f"Database health check failed with error: {e}")
        return False


async def check_redis_health(redis: Redis) -> bool:
    try:
        await redis.ping()
        return True
    except Exception as e:
        LOGGER.exception(f"Redis health check failed with error: {e}")
        return False
