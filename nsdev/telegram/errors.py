import traceback
from functools import wraps
from io import BytesIO

from ..utils.logger import LoggerHandler


class ErrorHandler:
    def __init__(self, client):
        self._client = client
        self._log = LoggerHandler()

    def handle(
        self,
        log_channel_id: int = None,
        error_message_template: str = "❌ Terjadi kesalahan:\n`{error}: {message}`",
        silent: bool = False,
    ):
        def decorator(func):
            @wraps(func)
            async def wrapped(client, message, *args, **kwargs):
                try:
                    return await func(client, message, *args, **kwargs)
                except Exception as e:
                    full_error = traceback.format_exc()
                    self._log.error(f"Exception in handler '{func.__name__}':\n{full_error}")

                    if log_channel_id:
                        try:
                            error_for_channel = f"⚠️ **Error in handler:** `{func.__name__}`\n\n**From User:** {message.from_user.mention}\n**Chat:** `{message.chat.title or message.chat.id}`\n\n**Traceback:**\n```{full_error}```"
                            if len(error_for_channel) > 4096:
                                log_file = BytesIO(full_error.encode())
                                log_file.name = f"error_{message.chat.id}_{message.id}.log"
                                await client.send_document(
                                    log_channel_id, document=log_file, caption=f"Error log for `{func.__name__}`"
                                )
                            else:
                                await client.send_message(log_channel_id, error_for_channel)
                        except Exception as log_e:
                            self._log.error(f"Failed to send error log to channel {log_channel_id}: {log_e}")

                    if not silent:
                        try:
                            user_error_msg = error_message_template.format(error=type(e).__name__, message=str(e))
                            await message.reply_text(user_error_msg, quote=True)
                        except Exception as reply_e:
                            self._log.error(f"Failed to send error reply to user: {reply_e}")

            return wrapped

        return decorator
