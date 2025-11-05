"""
🚀 Redis Client Configuration
Mock Redis client para testes quando Redis não está disponível
"""

import json
from typing import Optional, Any
import asyncio

class MockRedisClient:
    """Mock Redis client para desenvolvimento e testes"""

    def __init__(self):
        self._cache = {}

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        return self._cache.get(key)

    async def setex(self, key: str, seconds: int, value: str):
        """Set value with expiration (mock - não expira)"""
        self._cache[key] = value

    async def set(self, key: str, value: str):
        """Set value"""
        self._cache[key] = value

    async def delete(self, key: str):
        """Delete key"""
        if key in self._cache:
            del self._cache[key]

# Usar mock Redis para desenvolvimento/testes
redis_client = MockRedisClient()