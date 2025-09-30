import time
from functools import wraps
from typing import Dict, Tuple

from pyrogram.types import CallbackQuery, Message

from .gradient import Gradient


_user_timestamps: Dict[str, Tuple[int, float]] = {}


class RateLimiter(Gradient):
    def __init__(self, client):
        super().__init__()
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

                key = f"{user_id}:{id(func)}"

                current_time = time.time()

                if key in _user_timestamps:
                    count, last_time = _user_timestamps[key]

                    time_passed = current_time - last_time
                    if time_passed < per_seconds:
                        if count >= limit:
                            time_to_wait = per_seconds - time_passed
                            time_str = self.gettime(int(time_to_wait))
                            
                            fmt = client.ns.telegram.formatter(mode="html")
                            error_text = (
                                fmt.bold("⏳ Batas Penggunaan Tercapai ⏳")
                                .new_line(2)
                                .text("Anda telah mencapai batas penggunaan untuk perintah ini.")
                                .new_line()
                                .text(f"Silakan coba lagi dalam ")
                                .bold(time_str)
                                .text(".")
                            )

                            if isinstance(update, Message):
                                await update.reply_text(fmt.blockquote(error_text), quote=True)
                            elif isinstance(update, CallbackQuery):
                                await update.answer(
                                    f"Batas penggunaan tercapai. Coba lagi dalam {time_str}.",
                                    show_alert=True
                                )

                            return

                        _user_timestamps[key] = (count + 1, last_time)
                    else:
                        _user_timestamps[key] = (1, current_time)
                else:
                    _user_timestamps[key] = (1, current_time)

                return await func(client, update, *args, **kwargs)

            return wrapped

        return decorator
