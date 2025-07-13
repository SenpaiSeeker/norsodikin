import asyncio

import pyrogram

loop = asyncio.get_event_loop()


class UserCancelled(Exception):
    pass


pyrogram.errors.UserCancelled = UserCancelled


def patch(obj):
    def is_patchable(item):
        return getattr(item[1], "patchable", False)

    def wrapper(container):
        for name, func in filter(is_patchable, container.__dict__.items()):
            old = getattr(obj, name, None)
            setattr(obj, "old" + name, old)
            setattr(obj, name, func)
        return container

    return wrapper


def patchable(func):
    func.patchable = True
    return func


@patch(pyrogram.client.Client)
class Client:
    @patchable
    def __init__(self, *args, **kwargs):
        self._conversation_cache = {}
        self.old__init__(*args, **kwargs)

    @patchable
    async def _listen(self, chat_id, timeout=None):
        future = loop.create_future()
        self._conversation_cache[chat_id] = future

        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            raise
        finally:
            self._conversation_cache.pop(chat_id, None)

    @patchable
    async def _ask(self, chat_id, text, timeout=None, *args, **kwargs):
        await self.send_message(chat_id, text, *args, **kwargs)
        return await self._listen(chat_id, timeout)

    @patchable
    async def _resolve(self, client, message):
        chat_id = message.chat.id
        future = self._conversation_cache.get(chat_id)

        if future and not future.done():
            future.set_result(message)

    @patchable
    async def on_message(self, _, message):
        await self._resolve(self, message)


@patch(pyrogram.handlers.MessageHandler)
class MessageHandler:
    @patchable
    def __init__(self, callback, filters=None):
        self.old__init__(callback, filters)

    @patchable
    async def check(self, client, update):
        chat_id = update.chat.id
        future = client._conversation_cache.get(chat_id)

        if future and not future.done():
            return True
        return await self.filters(client, update) if callable(self.filters) else True


@patch(pyrogram.types.Chat)
class Chat:
    @patchable
    def ask(self, *args, **kwargs):
        return self._client._ask(self.id, *args, **kwargs)


@patch(pyrogram.types.User)
class User:
    @patchable
    def ask(self, *args, **kwargs):
        return self._client._ask(self.id, *args, **kwargs)
