import asyncio
from typing import Optional, Union, List
from pyrogram import Client, filters
from pyrogram.types import Message
from .exceptions import ListenerTimeout, ListenerStopped, ListenerCanceled

class ListenerManager:
    def __init__(self, client: Client):
        self.client = client
        self.listeners = {}

    async def listen(
        self,
        chat_id: Union[int, str],
        user_id: Optional[Union[int, str]] = None,
        filters=None,
        timeout: int = 300
    ) -> Message:
        future = asyncio.get_running_loop().create_future()
        
        chat_id = await self._resolve_id(chat_id)
        user_id = await self._resolve_id(user_id) if user_id else None

        listener_id = f"{chat_id}_{user_id}" if user_id else str(chat_id)
        
        self.listeners[listener_id] = future

        def _check(client, message):
            if message.chat.id == chat_id:
                if user_id and message.from_user.id != user_id:
                    return False
                if filters and not filters(client, message):
                    return False
                return True

        @self.client.on_message(group=999)
        async def _listener_handler(client, message):
            if not future.done() and _check(client, message):
                future.set_result(message)
                self.client.remove_handler(_listener_handler, group=999)
                if listener_id in self.listeners:
                    del self.listeners[listener_id]

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self.client.remove_handler(_listener_handler, group=999)
            if listener_id in self.listeners:
                del self.listeners[listener_id]
            raise ListenerTimeout("Waktu tunggu habis.")
        except asyncio.CancelledError:
            self.client.remove_handler(_listener_handler, group=999)
            if listener_id in self.listeners:
                del self.listeners[listener_id]
            raise ListenerCanceled("Listener dibatalkan.")

    async def ask(
        self,
        chat_id: Union[int, str],
        text: str,
        user_id: Optional[Union[int, str]] = None,
        filters=None,
        timeout: int = 300,
        **kwargs
    ) -> Message:
        sent_message = await self.client.send_message(chat_id, text, **kwargs)
        
        try:
            response = await self.listen(chat_id, user_id, filters, timeout)
            response.request = sent_message
            return response
        except Exception as e:
            raise e

    def cancel(self, chat_id: Union[int, str], user_id: Optional[Union[int, str]] = None):
        asyncio.create_task(self._cancel_async(chat_id, user_id))

    async def _cancel_async(self, chat_id, user_id):
        chat_id = await self._resolve_id(chat_id)
        user_id = await self._resolve_id(user_id) if user_id else None
        
        listener_id = f"{chat_id}_{user_id}" if user_id else str(chat_id)
        
        if listener_id in self.listeners:
            future = self.listeners[listener_id]
            if not future.done():
                future.cancel()
            del self.listeners[listener_id]

    async def _resolve_id(self, peer_id):
        if isinstance(peer_id, int):
            return peer_id
        try:
            chat = await self.client.get_chat(peer_id)
            return chat.id
        except:
            return peer_id
