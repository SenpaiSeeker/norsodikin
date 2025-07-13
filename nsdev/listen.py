import asyncio

import pyrogram


def patch(cls):
    def wrapper(subcls):
        for name, method in vars(subcls).items():
            if hasattr(method, "__is_patchable__"):
                old = getattr(cls, name, None)
                if old:
                    setattr(subcls, f"old_{name}", old)
                setattr(cls, name, method)
        return subcls

    return wrapper


def patchable(func):
    func.__is_patchable__ = True
    return func


loop = asyncio.get_event_loop()


class AskCancelled(Exception):
    pass


@patch(pyrogram.client.Client)
class Client:
    @patchable
    def __init__(self, *args, **kwargs):
        self._listeners = {}
        self.old__init__(*args, **kwargs)

    @patchable
    async def listen(self, chat_id, filters=None, timeout=None):
        if not isinstance(chat_id, int):
            chat = await self.get_chat(chat_id)
            chat_id = chat.id

        future = loop.create_future()
        future.add_done_callback(lambda fut: self._listeners.pop(chat_id, None))
        self._listeners[chat_id] = {"future": future, "filters": filters}
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError as e:
            if chat_id in self._listeners:
                self.cancel_listener(chat_id)
            raise AskCancelled("Ask timed out") from e

    @patchable
    async def ask(self, chat_id, text, filters=None, timeout=None, **kwargs):
        request = await self.send_message(chat_id, text, **kwargs)
        response = await self.listen(chat_id, filters, timeout)
        response.request = request
        return response

    @patchable
    def cancel_listener(self, chat_id):
        listener = self._listeners.get(chat_id)
        if not listener:
            return
        future = listener["future"]
        if not future.done():
            future.set_exception(AskCancelled("Listener cancelled"))
        self._listeners.pop(chat_id, None)


@patch(pyrogram.types.Chat)
class Chat:
    @patchable
    def listen(self, *args, **kwargs):
        return self._client.listen(self.id, *args, **kwargs)

    @patchable
    def ask(self, *args, **kwargs):
        return self._client.ask(self.id, *args, **kwargs)

    @patchable
    def cancel_listener(self):
        return self._client.cancel_listener(self.id)


@patch(pyrogram.types.User)
class User:
    @patchable
    def listen(self, *args, **kwargs):
        return self._client.listen(self.id, *args, **kwargs)

    @patchable
    def ask(self, *args, **kwargs):
        return self._client.ask(self.id, *args, **kwargs)

    @patchable
    def cancel_listener(self):
        return self._client.cancel_listener(self.id)
