import redis
import os
import logging
from typing import Optional

# Configurar Logging
logger = logging.getLogger(__name__)

class RedisService:
    _instance = None

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.prefix: str = os.getenv("REDIS_PREFIX", "APP") 

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def connect(self):
        """Inicializa la conexión a Redis."""
        if self.client:
            return # Ya conectado

        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            redis_db = int(os.getenv("REDIS_DB", 0))
            redis_password = os.getenv("REDIS_PASSWORD", None)

            self.client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True 
            )
            # Ping para verificar conexión
            self.client.ping()
            logger.info(f"Conectado a Redis en {redis_host}:{redis_port}/{redis_db}")

        except redis.RedisError as e:
            logger.critical(f"Error CRÍTICO al conectar a Redis: {e}")
            self.client = None

    def close(self):
        """Cierra la conexión a Redis."""
        if self.client:
            try:
                self.client.close()
                logger.info("Conexión a Redis cerrada.")
            except redis.RedisError as e:
                logger.error(f"Error al cerrar conexión Redis: {e}")
            finally:
                self.client = None

    def _get_key(self, key: str) -> str:
        
        return f"{self.prefix}:{key}"

    def get(self, key: str) -> Optional[str]:
        if not self.client: return None
        try:
            return self.client.get(self._get_key(key))
        except redis.RedisError as e:
            logger.error(f"Redis Error (GET): {e}")
            return None

    def set(self, key: str, value: str, ttl: int = 60) -> bool:
        if not self.client: return False
        try:
            return self.client.set(self._get_key(key), value, ex=ttl)
        except redis.RedisError as e:
            logger.error(f"Redis Error (SET): {e}")
            return False

    def delete(self, key: str) -> bool:
        if not self.client: return False
        try:
            return self.client.delete(self._get_key(key)) > 0
        except redis.RedisError as e:
            logger.error(f"Redis Error (DELETE): {e}")
            return False

    def delete_pattern(self, pattern: str):
        if not self.client: return
        try:
          
            full_pattern = self._get_key(pattern)
            keys = list(self.client.scan_iter(match=full_pattern))
            if keys:
                self.client.delete(*keys)
        except redis.RedisError as e:
            logger.error(f"Redis Error (DELETE PATTERN): {e}")


redis_service = RedisService.get_instance()
