"""Simple in-memory cache for development"""

import time
from typing import Dict, Any, Optional

class SimpleCache:
    """Simple in-memory cache for development"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = 300  # 5 minutes
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self._cache:
            item = self._cache[key]
            if time.time() < item['expires']:
                return item['value']
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        ttl_value = ttl if ttl is not None else self.default_ttl
        expires = time.time() + ttl_value
        self._cache[key] = {'value': value, 'expires': expires}
    
    def delete(self, key: str):
        """Delete from cache"""
        if key in self._cache:
            del self._cache[key]

# Global cache instance
cache = SimpleCache()