import time
from functools import wraps
from typing import Dict, Tuple

from pyrogram.types import CallbackQuery, Message


_user_timestamps: Dict[str, Tuple[int, float]] = {}


class RateLimiter:
    def __init__(self, client):
        self._client = client

    def __call__(self, limit: int, per_seconds: int):
        def decorator(func):
            @wraps(func)
            async def wrapped(client, update, *args, **kwargs):
                if isinstance(update, Message):
                    user_id = update.from_user.id
                elif isinstance(update, CallbackQuery):
                    user_id = update.from_user.id
                else:
                    return await func(client, update, *args, **kwargs)

                key = f"{user_id}:{func.__name__}"
                
                current_time = time.time()
                
                if key in _user_timestamps:
                    count, last_time = _user_timestamps[key]
                    
                    time_passed = current_time - last_time
                    if time_passed < per_seconds:
                        if count >= limit:
                            time_to_wait = per_seconds - time_passed
                            error_text = f"Anda terlalu cepat! Silakan coba lagi dalam {int(time_to_wait)} detik."
                            
                            if isinstance(update, Message):
                                await update.reply_text(error_text, quote=True)
                            elif isinstance(update, CallbackQuery):
                                await update.answer(error_text, show_alert=True)
                            
                            return
                        
                        _user_timestamps[key] = (count + 1, last_time)
                    else:
                        _user_timestamps[key] = (1, current_time)
                else:
                    _user_timestamps[key] = (1, current_time)
                
                return await func(client, update, *args, **kwargs)
            return wrapped
        return decorator
