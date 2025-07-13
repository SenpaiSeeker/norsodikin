import asyncio

import pyrogram


class ListenerTimeout(Exception):
    pass


class Listener:
    def __init__(self, client: pyrogram.Client):
        self.client = client
        self.handlers = {}

    async def listen(
        self, chat_id: int, user_id: int = None, filters: "pyrogram.filters.Filter" = None, timeout: int = None
    ) -> "pyrogram.types.Message":

        if user_id is None:
            user_id = chat_id

        queue = asyncio.Queue(1)

        combined_filters = pyrogram.filters.chat(chat_id) & pyrogram.filters.user(user_id)
        if filters:
            combined_filters &= filters

        async def callback(_, message: pyrogram.types.Message):
            await queue.put(message)

        handler = pyrogram.handlers.MessageHandler(callback, filters=combined_filters)

        group = -1
        self.client.add_handler(handler, group)

        try:
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            raise ListenerTimeout(f"Batas waktu {timeout} detik terlampaui.")
        finally:
            self.client.remove_handler(handler, group)

    async def ask(
        self,
        chat_id: int,
        text: str,
        user_id: int = None,
        filters: "pyrogram.filters.Filter" = None,
        timeout: int = 30,
        **kwargs,
    ) -> "pyrogram.types.Message":

        if user_id is None:
            user_id = chat_id

        request_message = await self.client.send_message(chat_id, text, **kwargs)

        response_message = await self.listen(chat_id=chat_id, user_id=user_id, filters=filters, timeout=timeout)

        setattr(response_message, "request", request_message)
        return response_message
