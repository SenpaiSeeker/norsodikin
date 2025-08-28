import asyncio
from contextlib import asynccontextmanager

from pyrogram.enums import ChatAction


class TelegramActions:
    def __init__(self, client):
        self.client = client

    @asynccontextmanager
    async def _action_context(self, chat_id, action: ChatAction):
        if not self.client or not self.client.is_connected:
            yield
            return

        async def send_action_loop():
            while True:
                try:
                    await self.client.send_chat_action(chat_id, action)
                    await asyncio.sleep(5)
                except asyncio.CancelledError:
                    break
                except Exception:
                    break

        task = asyncio.create_task(send_action_loop())
        try:
            yield
        except Exception as e:
            raise e
        finally:
            task.cancel()

    def typing(self, chat_id):
        return self._action_context(chat_id, ChatAction.TYPING)

    def upload_photo(self, chat_id):
        return self._action_context(chat_id, ChatAction.UPLOAD_PHOTO)

    def upload_video(self, chat_id):
        return self._action_context(chat_id, ChatAction.UPLOAD_VIDEO)

    def record_video(self, chat_id):
        return self._action_context(chat_id, ChatAction.RECORD_VIDEO)

    def record_voice(self, chat_id):
        return self._action_context(chat_id, ChatAction.RECORD_VOICE)
