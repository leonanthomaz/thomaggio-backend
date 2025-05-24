# app/utils/cache.py
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from app.configuration.settings import Configuration

Configuration()

class DataCache:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._expiry_times: Dict[str, datetime] = {}
        self.default_ttl = timedelta(minutes=15)

    def set(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Armazena dados no cache com tempo de expiração em segundos."""
        expiration = datetime.now() + timedelta(seconds=ttl) if ttl else datetime.now() + self.default_ttl
        self._cache[key] = data
        self._expiry_times[key] = expiration
        logging.debug(f"Cache setado para key: {key}")

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Obtém dados do cache se existirem e não estiverem expirados."""
        if key not in self._cache:
            return None
            
        if datetime.now() > self._expiry_times.get(key, datetime.min):
            del self._cache[key]
            del self._expiry_times[key]
            logging.debug(f"Cache expirado para key: {key}")
            return None
            
        return self._cache[key]

    def clear(self, key: str) -> None:
        """Remove dados do cache."""
        if key in self._cache:
            del self._cache[key]
            del self._expiry_times[key]
            logging.debug(f"Cache limpo para key: {key}")

