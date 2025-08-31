import time
from functools import wraps
from typing import Dict, Tuple

_user_timestamps: Dict[str, Tuple[int, float]] = {}


class RateLimiter:
    def __init__(self, client):
        self._client = client

    def __call__(self, limit: int, per_seconds: int):
        def decorator(func):
            @wraps(func)
            async def wrapped(client, message, *args, **kwargs):
                user_id = message.from_user.id
                chat_id = message.chat.id
                key = f"{user_id}:{func.__name__}"
                
                current_time = time.time()
                
                if key in _user_timestamps:
                    count, last_time = _user_timestamps[key]
                    
                    time_passed = current_time - last_time
                    if time_passed < per_seconds:
                        if count >= limit:
                            time_to_wait = per_seconds - time_passed
                            await message.reply_text(
                                f"Anda terlalu cepat! Silakan coba lagi dalam **{int(time_to_wait)} detik**.",
                                quote=True
                            )
                            return
                        
                        _user_timestamps[key] = (count + 1, last_time)
                    else:
                        _user_timestamps[key] = (1, current_time)
                else:
                    _user_timestamps[key] = (1, current_time)
                
                return await func(client, message, *args, **kwargs)
            return wrapped
        return decorator
