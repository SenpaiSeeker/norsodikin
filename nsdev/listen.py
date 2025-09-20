import asyncio
import functools

import pyrogram
from pyrogram import filters

class UserCancelled(Exception):
    pass

pyrogram.errors.UserCancelled = UserCancelled

_LISTEN_GROUP = -69420

async def _listen_callback(client, message, future, filters):
    if await filters(client, message):
        if not future.done():
            future.set_result(message)

def patch_pyrogram_client():
    if hasattr(pyrogram.Client, "_listen_patched"):
        return

    async def listen(self, chat_id, timeout=None, filters=None):
        if not isinstance(chat_id, int):
            try:
                chat = await self.get_chat(chat_id)
                chat_id = chat.id
            except Exception as e:
                raise ValueError(f"Could not get chat_id for {chat_id}: {e}")

        combined_filters = filters.chat(chat_id)
        if filters:
            combined_filters &= filters

        future = asyncio.get_running_loop().create_future()
        handler = pyrogram.handlers.MessageHandler(
            _listen_callback,
            filters=combined_filters
        )
        
        self.add_handler(handler, group=_LISTEN_GROUP)
        
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            if not future.done():
                future.set_exception(asyncio.TimeoutError())
            raise
        finally:
            self.remove_handler(handler, group=_LISTEN_GROUP)

    async def ask(self, chat_id, text, timeout=None, filters=None, **kwargs):
        request = await self.send_message(chat_id, text, **kwargs)
        response = await self.listen(chat_id, timeout, filters)
        response.request = request
        return response

    pyrogram.Client.listen = listen
    pyrogram.Client.ask = ask
    pyrogram.Client._listen_patched = True

    async def chat_ask(self, text, timeout=None, filters=None, **kwargs):
        return await self._client.ask(self.id, text, timeout, filters, **kwargs)

    pyrogram.types.Chat.ask = chat_ask
    pyrogram.types.User.ask = chat_ask

patch_pyrogram_client()
