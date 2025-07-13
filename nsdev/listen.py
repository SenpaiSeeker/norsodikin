import asyncio
from typing import Optional

import pyrogram
from pyrogram.client import Client
from pyrogram.filters import Filter
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message


class ListenerTimeout(Exception):
    pass


class ListenerCanceled(Exception):
    pass


async def ask(self: Client, chat_id: int, text: str, filters: Optional[Filter] = None, timeout: int = 30) -> Message:
    future = asyncio.get_running_loop().create_future()

    async def a_callback(_, message: Message):
        if not future.done():
            future.set_result(message)

    internal_filters = pyrogram.filters.chat(chat_id) & pyrogram.filters.user(chat_id)

    combined_filters = internal_filters
    if filters:
        combined_filters = internal_filters & filters

    handler = MessageHandler(a_callback, filters=combined_filters)
    self.add_handler(handler, group=-1)

    try:
        request_message = await self.send_message(chat_id, text)

        response_message = await asyncio.wait_for(future, timeout=timeout)

        setattr(response_message, "request", request_message)

    except asyncio.TimeoutError:
        raise ListenerTimeout(f"Batas waktu {timeout} detik terlampaui.")
    finally:
        self.remove_handler(handler, group=-1)


Client.ask = ask
