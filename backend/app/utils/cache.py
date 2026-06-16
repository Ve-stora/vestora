"""
Simple in-memory TTL cache.
Drop-in replacement interface 

async def cache_get(key: str) -> Optional[Any]:
   return await cache.get(key)


async def cache_set(key: str, value: Any, ttl: int) -> None:
   await cache.set(key, value, ttl)


async def cache_delete(key: str) -> None:
   await cache.delete(key)