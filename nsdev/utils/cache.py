import asyncio
import time
from functools import wraps

_cache = {}

def memoize(ttl: int):
    def decorator(func):
        @wraps(func)
        async def wrapped(*args, **kwargs):
            key_parts = [func.__name__] + list(args) + sorted(kwargs.items())
            key = str(key_parts)
            
            current_time = time.time()
            
            if key in _cache:
                result, timestamp = _cache[key]
                if current_time - timestamp < ttl:
                    return result
            
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
                
            _cache[key] = (result, current_time)
            return result
        return wrapped
    return decorator

def clear_cache():
    _cache.clear()
