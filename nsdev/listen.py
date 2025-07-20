import asyncio
import functools

import pyrogram


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


class UserCancelled(Exception):
    pass


pyrogram.errors.UserCancelled = UserCancelled


@patch(pyrogram.client.Client)
class Client:
    @patchable
    def __init__(self, *args, **kwargs):
        self._conversations = {}
        self.old__init__(*args, **kwargs)

    @patchable
    async def listen(self, chat_id, timeout=None):
        if not isinstance(chat_id, int):
            try:
                chat = await self.get_chat(chat_id)
                chat_id = chat.id
            except Exception as e:
                raise ValueError(f"Could not get chat_id for {chat_id}: {e}")

        loop = asyncio.get_running_loop()
        future = loop.create_future()

        future.add_done_callback(functools.partial(self._clear, chat_id))
        self._conversations[chat_id] = future

        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            self.cancel(chat_id, future)
            raise

    @patchable
    async def ask(self, chat_id, text, timeout=None, **kwargs):
        request = await self.send_message(chat_id, text, **kwargs)
        response = await self.listen(chat_id, timeout)
        response.request = request
        return response

    @patchable
    def _clear(self, chat_id, future):
        if chat_id in self._conversations and self._conversations[chat_id] is future:
            del self._conversations[chat_id]

    @patchable
    def cancel(self, chat_id, future_to_cancel=None):
        future = self._conversations.get(chat_id)
        if future and not future.done() and (not future_to_cancel or future is future_to_cancel):
            future.set_exception(UserCancelled())
            self._clear(chat_id, future)


@patch(pyrogram.handlers.MessageHandler)
class MessageHandler:
    @patchable
    def __init__(self, callback, filters=None):
        self._user_callback = callback
        self.old__init__(self._resolver, filters)

    @patchable
    async def _resolver(self, client, message, *args):
        future = client._conversations.get(message.chat.id)
        if future and not future.done():
            future.set_result(message)
        else:
            await self._user_callback(client, message, *args)

    @patchable
    async def check(self, client, update):
        if update.chat and client._conversations.get(update.chat.id):
            return True
        return await self.filters(client, update) if callable(self.filters) else True


@patch(pyrogram.types.Chat)
class Chat:
    @patchable
    def listen(self, *args, **kwargs):
        return self._client.listen(self.id, *args, **kwargs)

    @patchable
    def cancel(self):
        return self._client.cancel(self.id)

    @patchable
    async def ask(self, text, timeout=None, **kwargs):
        request = await self._client.send_message(self.id, text, **kwargs)
        response = await self.listen(timeout=timeout)
        response.request = request
        return response


@patch(pyrogram.types.User)
class User:
    @patchable
    def listen(self, *args, **kwargs):
        return self._client.listen(self.id, *args, **kwargs)

    @patchable
    def cancel(self):
        return self._client.cancel(self.id)

    @patchable
    async def ask(self, text, timeout=None, **kwargs):
        request = await self._client.send_message(self.id, text, **kwargs)
        response = await self.listen(timeout=timeout)
        response.request = request
        return response
