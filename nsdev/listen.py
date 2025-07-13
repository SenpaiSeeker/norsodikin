import asyncio
from typing import Optional

from pyrogram.client import Client
from pyrogram.filters import Filter
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message


class ListenerTimeout(Exception):
    pass


class ListenerCanceled(Exception):
    pass


class Conversation:
    def __init__(self, client: Client, chat_id: int, user_id: int, filters: Optional[Filter], timeout: Optional[int]):
        self.client = client
        self.chat_id = chat_id
        self.user_id = user_id
        self.filters = filters
        self.timeout = timeout
        self.queue = asyncio.Queue(1)
        self.handler = None
        self.task = None

    async def start(self):
        self.handler = MessageHandler(self._on_message, self.filters)
        self.client.add_handler(self.handler, group=-1)

        try:
            return await asyncio.wait_for(self.queue.get(), timeout=self.timeout)
        except asyncio.TimeoutError:
            raise ListenerTimeout(f"Batas waktu {self.timeout} detik terlampaui.")
        finally:
            self.stop()

    def stop(self):
        if self.handler:
            self.client.remove_handler(self.handler, group=-1)
            self.handler = None

    async def _on_message(self, _, message: Message):
        if message.chat.id == self.chat_id and message.from_user.id == self.user_id:
            await self.queue.put(message)


async def ask(
    self: Client,
    chat_id: int,
    text: str,
    filters: Optional[Filter] = None,
    timeout: int = 30,
    user_id: Optional[int] = None,
    *args,
    **kwargs,
) -> Message:
    if user_id is None:
        user_id = chat_id

    conversation = Conversation(client=self, chat_id=chat_id, user_id=user_id, filters=filters, timeout=timeout)

    request_message = await self.send_message(chat_id, text, *args, **kwargs)
    response_message = await conversation.start()

    # Menambahkan pesan pertanyaan ke dalam pesan jawaban.
    setattr(response_message, "request", request_message)

    return response_message


Client.ask = ask
