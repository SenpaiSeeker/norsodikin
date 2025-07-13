import asyncio

import pyrogram


class ListenerCanceled(Exception):
    pass


pyrogram.errors.ListenerCanceled = ListenerCanceled

loop = asyncio.get_event_loop()


def patchable(func):
    func._patchable = True
    return func


def patch(target):
    def wrapper(container):
        for name, func in container.__dict__.items():
            if getattr(func, "_patchable", False):
                setattr(target, name, func)
        return container

    return wrapper


@patch(pyrogram.client.Client)
class ClientPatch:
    @patchable
    async def listen(self, chat_id: int, filters=None, timeout: float = None):
        if not isinstance(chat_id, int):
            chat = await self.get_chat(chat_id)
            chat_id = chat.id

        future = loop.create_future()
        future.add_done_callback(lambda f: self._clear_listener(chat_id))
        self._listeners.setdefault(chat_id, []).append((future, filters))

        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            future.cancel()
            raise ListenerCanceled()

    @patchable
    async def ask(self, chat_id: int, text: str, filters=None, timeout: float = None, **kwargs):
        request = await self.send_message(chat_id, text, **kwargs)
        response = await self.listen(chat_id, filters, timeout)
        response.request = request
        return response

    @patchable
    def _clear_listener(self, chat_id: int):
        self._listeners.pop(chat_id, None)

    @patchable
    def _dispatch_update(self, update):
        message = update
        chat_id = message.chat.id
        listeners = self._listeners.get(chat_id, [])
        for future, filters in list(listeners):
            if future.done():
                continue
            try:
                ok = filters(self, message) if callable(filters) else True
            except Exception:
                ok = True
            if ok:
                future.set_result(message)
                return
        return self.old__dispatch_update(update)


@patch(pyrogram.client.Client)
class InitPatch:
    @patchable
    def __init__(self, *args, **kwargs):
        self._listeners = {}
        self.old__init__(*args, **kwargs)


for _cls in (pyrogram.types.Chat, pyrogram.types.User):

    def _make(method_name):
        async def method(self, *args, **kwargs):
            return await getattr(self._client, method_name)(self.id, *args, **kwargs)

        return method

    setattr(_cls, "tanya", _make("ask"))
    setattr(_cls, "listen", _make("listen"))
    setattr(_cls, "cancel_listener", lambda self: self._client._clear_listener(self.id))
