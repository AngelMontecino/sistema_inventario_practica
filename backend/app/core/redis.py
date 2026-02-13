import redis
import os
import logging
from typing import Optional

# Configurar Logging
logger = logging.getLogger(__name__)

# Pool de Conexión Redis
redis_pool: Optional[redis.Redis] = None

def get_redis_client() -> redis.Redis:
    global redis_pool
    if redis_pool is None:
        redis_host = os.getenv("REDIS_HOST")
        redis_port = int(os.getenv("REDIS_PORT"))
        redis_db = int(os.getenv("REDIS_DB"))
        redis_password = os.getenv("REDIS_PASSWORD")

        redis_pool = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True 
        )
    return redis_pool

def get_cache(key: str) -> Optional[str]:
    client = get_redis_client()
    try:
        return client.get(key)
    except redis.RedisError as e:
        logger.error(f"Redis Error (GET): {e}")
        return None

def set_cache(key: str, value: str, ttl: int = 60) -> bool:
    client = get_redis_client()
    try:
        return client.set(key, value, ex=ttl)
    except redis.RedisError as e:
        logger.error(f"Redis Error (SET): {e}")
        return False

def delete_cache(key: str) -> bool:
    """Elimina una clave específica directamente"""
    client = get_redis_client()
    try:
        return client.delete(key) > 0
    except redis.RedisError as e:
        logger.error(f"Redis Error (DELETE): {e}")
        return False

def delete_cache_pattern(pattern: str):

    client = get_redis_client()
    try:
        
        keys = list(client.scan_iter(match=pattern))
        if keys:
            client.delete(*keys)
    except redis.RedisError as e:
        logger.error(f"Redis Error (DELETE PATTERN): {e}")
