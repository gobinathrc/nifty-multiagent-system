"""In-Memory Query Cache."""

import hashlib
import time
from typing import Optional, Dict, Any


class ResponseCache:
    """Caches query responses by normalized hash to eliminate token waste."""

    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds

    @staticmethod
    def _normalize(query: str) -> str:
        cleaned = query.lower().strip().rstrip("?!., ")
        return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

    def get(self, query: str) -> Optional[str]:
        key = self._normalize(query)
        entry = self.cache.get(key)
        if entry:
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["response"]
            else:
                del self.cache[key]
        return None

    def set(self, query: str, response: str) -> None:
        key = self._normalize(query)
        self.cache[key] = {
            "response": response,
            "timestamp": time.time(),
        }
