import os
import asyncio
from redis.asyncio import Redis
from app.core.config import settings

# Criar cliente Redis assíncrono
redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_redis():
    """Get async Redis client"""
    return redis_client

async def close_redis():
    """Close Redis connection"""
    await redis_client.aclose()

# Fallback para desenvolvimento sem Redis
class NoOpRedisClient:
    """Cliente Redis No-Op para desenvolvimento"""

    async def ping(self):
        return True

    async def get(self, key):
        return None

    async def set(self, key, value):
        return True

    async def setex(self, key, time, value):
        return True

    async def delete(self, key):
        return True

    async def exists(self, key):
        return False

    async def close(self):
        pass

    async def aclose(self):
        pass

# Usar cliente No-Op se em modo dev sem Redis
if os.getenv("DEV_MODE_NO_REDIS", "false").lower() == "true":
    redis_client = NoOpRedisClient()