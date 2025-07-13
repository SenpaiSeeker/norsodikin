import asyncio

import pyrogram


class UserCancelled(Exception):
    pass


pyrogram.errors.UserCancelled = UserCancelled

loop = asyncio.get_event_loop()


def patch(obj):
    def is_patchable(item):
        return getattr(item[1], "patchable", False)

    def wrapper(container):
        for name, func in filter(is_patchable, container.__dict__.items()):
            old = getattr(obj, name, None)
            setattr(obj, "old_" + name, old)
            setattr(obj, name, func)
        return container

    return wrapper


def patchable(func):
    func.patchable = True
    return func


@patch(pyrogram.Client)
class Client:
    @patchable
    def __init__(self, *args, **kwargs):
        self._conversations = {}
        self.old___init__(*args, **kwargs)

    @patchable
    async def listen(self, chat_id: int, timeout: int = 600):
        future = loop.create_future()
        self._conversations[chat_id] = future
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            raise
        finally:
            self._conversations.pop(chat_id, None)

    @patchable
    async def ask(self, chat_id: int, text: str, timeout: int = 600, *args, **kwargs):
        request = await self.send_message(chat_id, text, *args, **kwargs)
        response = await self.listen(chat_id, timeout)
        response.request = request
        return response

    @patchable
    def cancel_listener(self, chat_id: int):
        future = self._conversations.get(chat_id)
        if future and not future.done():
            future.set_exception(UserCancelled())
            self._conversations.pop(chat_id, None)


@patch(pyrogram.handlers.MessageHandler)
class MessageHandler:
    @patchable
    def __init__(self, callback, filters=None):
        self._user_callback = callback
        self.old___init__(self._resolve_conversation, filters)

    @patchable
    async def _resolve_conversation(self, client, message, *args):
        future = getattr(client, "_conversations", {}).get(message.chat.id)
        if future and not future.done():
            future.set_result(message)
        else:
            await self._user_callback(client, message, *args)


@patch(pyrogram.types.Chat)
class Chat:
    @patchable
    def ask(self, *args, **kwargs):
        return self._client.ask(self.id, *args, **kwargs)

    @patchable
    def listen(self, *args, **kwargs):
        return self._client.listen(self.id, *args, **kwargs)

    @patchable
    def cancel_listener(self):
        return self._client.cancel_listener(self.id)
