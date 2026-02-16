import json
from datetime import timedelta
from typing import List, Optional

import redis.asyncio as redis


class PermissionCache:
    """
    Centralized permission cache using Redis
    All services share this cache
    """

    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = timedelta(hours=1)  # Cache expires after 1 hour

    def _user_permission_key(self, user_id: str) -> str:
        """Generate Redis key for user permissions"""
        return f"user_permissions:{user_id}"

    def _user_roles_key(self, user_id: str) -> str:
        """Generate Redis key for user roles"""
        return f"user_roles:{user_id}"

    async def get_user_permissions(self, user_id: str) -> Optional[List[str]]:
        """Get user permissions from cache"""
        key = self._user_permission_key(user_id)
        data = await self.redis_client.get(key)

        if data:
            return json.loads(data)
        return None

    async def set_user_roles(
        self, user_id: str, roles: List[str], ttl: Optional[timedelta] = None
    ):
        """Store user roles in cache"""
        key = self._user_roles_key(user_id)
        await self.redis_client.setex(key, ttl or self.default_ttl, json.dumps(roles))

    async def close(self):
        """Close Redis connection"""
        await self.redis_client.close()


# Global cache instance
permission_cache: Optional[PermissionCache] = None


async def get_permission_cache() -> PermissionCache:
    """Dependency to get permission cache"""
    global permission_cache
    if permission_cache is None:
        from app.core.config import settings

        permission_cache = PermissionCache(settings.REDIS_CACHE_URL)
    return permission_cache
