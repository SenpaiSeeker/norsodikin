import asyncio
import functools
from typing import Union, List, Optional, Any, Dict, Callable

import pyrogram


def patch(obj: Any) -> Callable[[Any], Any]:
    def is_patchable(item: Any) -> bool:
        return getattr(item[1], "patchable", False)

    def wrapper(container: Any) -> Any:
        for name, func in filter(is_patchable, container.__dict__.items()):
            old = getattr(obj, name, None)
            setattr(obj, "old" + name, old)
            setattr(obj, name, func)
        return container

    return wrapper


def patchable(func: Callable[..., Any]) -> Callable[..., Any]:
    func.patchable = True
    return func


class UserCancelled(Exception):
    pass


pyrogram.errors.UserCancelled = UserCancelled


@patch(pyrogram.client.Client)
class Client:
    @patchable
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._conversations: Dict[Union[int, str], Any] = {}
        self.old__init__(*args, **kwargs)

        async def conversation_resolver(_: Any, message: pyrogram.types.Message) -> None:
            future = self._conversations.get(message.chat.id)
            if future:
                if isinstance(future, asyncio.Queue):
                    await future.put(message)
                    raise pyrogram.StopPropagation
                elif not future.done():
                    future.set_result(message)
                    raise pyrogram.StopPropagation

        self.add_handler(
            pyrogram.handlers.MessageHandler(conversation_resolver),
            group=-666,
        )

    @patchable
    async def listen(
        self,
        chat_id: Union[int, str],
        timeout: Optional[Union[int, float]] = None
    ) -> pyrogram.types.Message:
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
    async def ask(
        self,
        chat_id: Union[int, str],
        text: str,
        timeout: Optional[Union[int, float]] = None,
        **kwargs: Any
    ) -> pyrogram.types.Message:
        request = await self.send_message(chat_id, text, **kwargs)
        response = await self.listen(chat_id, timeout)
        response.request = request
        return response

    @patchable
    async def listen_batch(
        self,
        chat_id: Union[int, str],
        timeout: Optional[Union[int, float]] = None,
        is_done: Union[str, List[str]] = "/done",
        is_cancel: Union[str, List[str]] = "/cancel",
        notify_format: Optional[str] = "Pesan berhasil ditambahkan ke antrean. Total: {count}",
    ) -> List[pyrogram.types.Message]:
        if not isinstance(chat_id, int):
            try:
                chat = await self.get_chat(chat_id)
                chat_id = chat.id
            except Exception as e:
                raise ValueError(f"Could not get chat_id for {chat_id}: {e}")

        queue = asyncio.Queue()
        self._conversations[chat_id] = queue

        def normalize(val: Union[str, List[str], tuple, set]) -> List[str]:
            if isinstance(val, (list, tuple, set)):
                return [str(v).lower().strip() for v in val]
            return [str(val).lower().strip()]

        done_cmds = normalize(is_done)
        cancel_cmds = normalize(is_cancel)

        collected = []
        try:
            while True:
                if timeout:
                    msg = await asyncio.wait_for(queue.get(), timeout)
                else:
                    msg = await queue.get()

                if isinstance(msg, Exception):
                    raise msg

                text_val = (msg.text or "").lower().strip()
                if text_val in done_cmds:
                    return collected
                elif text_val in cancel_cmds:
                    collected.clear()
                    raise UserCancelled()
                else:
                    collected.append(msg)
                    if notify_format:
                        try:
                            notification = notify_format.format(
                                count=len(collected)
                            )
                            await msg.reply(notification, quote=True)
                        except Exception:
                            pass
        finally:
            if self._conversations.get(chat_id) is queue:
                del self._conversations[chat_id]

    @patchable
    async def ask_batch(
        self,
        chat_id: Union[int, str],
        text: str,
        timeout: Optional[Union[int, float]] = None,
        is_done: Union[str, List[str]] = "/done",
        is_cancel: Union[str, List[str]] = "/cancel",
        notify_format: Optional[str] = "Pesan berhasil ditambahkan ke antrean. Total: {count}",
        **kwargs: Any
    ) -> List[pyrogram.types.Message]:
        await self.send_message(chat_id, text, **kwargs)
        return await self.listen_batch(
            chat_id=chat_id,
            timeout=timeout,
            is_done=is_done,
            is_cancel=is_cancel,
            notify_format=notify_format,
        )

    @patchable
    def _clear(self, chat_id: Union[int, str], future: Any) -> None:
        if chat_id in self._conversations and self._conversations[chat_id] is future:
            del self._conversations[chat_id]

    @patchable
    def cancel(self, chat_id: Union[int, str], future_to_cancel: Optional[Any] = None) -> None:
        future = self._conversations.get(chat_id)
        if future and (not future_to_cancel or future is future_to_cancel):
            if isinstance(future, asyncio.Queue):
                future.put_nowait(UserCancelled())
            elif not future.done():
                future.set_exception(UserCancelled())
                self._clear(chat_id, future)


@patch(pyrogram.types.Chat)
class Chat:
    @patchable
    async def listen(self, *args: Any, **kwargs: Any) -> pyrogram.types.Message:
        return await self._client.listen(self.id, *args, **kwargs)

    @patchable
    def cancel(self) -> None:
        return self._client.cancel(self.id)

    @patchable
    async def ask(
        self,
        text: str,
        timeout: Optional[Union[int, float]] = None,
        **kwargs: Any
    ) -> pyrogram.types.Message:
        request = await self._client.send_message(self.id, text, **kwargs)
        response = await self.listen(timeout=timeout)
        response.request = request
        return response

    @patchable
    async def listen_batch(
        self,
        timeout: Optional[Union[int, float]] = None,
        is_done: Union[str, List[str]] = "/done",
        is_cancel: Union[str, List[str]] = "/cancel",
        notify_format: Optional[str] = "Pesan berhasil ditambahkan ke antrean. Total: {count}",
    ) -> List[pyrogram.types.Message]:
        return await self._client.listen_batch(
            self.id, timeout, is_done, is_cancel, notify_format
        )

    @patchable
    async def ask_batch(
        self,
        text: str,
        timeout: Optional[Union[int, float]] = None,
        is_done: Union[str, List[str]] = "/done",
        is_cancel: Union[str, List[str]] = "/cancel",
        notify_format: Optional[str] = "Pesan berhasil ditambahkan ke antrean. Total: {count}",
        **kwargs: Any
    ) -> List[pyrogram.types.Message]:
        return await self._client.ask_batch(
            self.id, text, timeout, is_done, is_cancel, notify_format, **kwargs
        )


@patch(pyrogram.types.User)
class User:
    @patchable
    async def listen(self, *args: Any, **kwargs: Any) -> pyrogram.types.Message:
        return await self._client.listen(self.id, *args, **kwargs)

    @patchable
    def cancel(self) -> None:
        return self._client.cancel(self.id)

    @patchable
    async def ask(
        self,
        text: str,
        timeout: Optional[Union[int, float]] = None,
        **kwargs: Any
    ) -> pyrogram.types.Message:
        request = await self._client.send_message(self.id, text, **kwargs)
        response = await self.listen(timeout=timeout)
        response.request = request
        return response

    @patchable
    async def listen_batch(
        self,
        timeout: Optional[Union[int, float]] = None,
        is_done: Union[str, List[str]] = "/done",
        is_cancel: Union[str, List[str]] = "/cancel",
        notify_format: Optional[str] = "Pesan berhasil ditambahkan ke antrean. Total: {count}",
    ) -> List[pyrogram.types.Message]:
        return await self._client.listen_batch(
            self.id, timeout, is_done, is_cancel, notify_format
        )

    @patchable
    async def ask_batch(
        self,
        text: str,
        timeout: Optional[Union[int, float]] = None,
        is_done: Union[str, List[str]] = "/done",
        is_cancel: Union[str, List[str]] = "/cancel",
        notify_format: Optional[str] = "Pesan berhasil ditambahkan ke antrean. Total: {count}",
        **kwargs: Any
    ) -> List[pyrogram.types.Message]:
        return await self._client.ask_batch(
            self.id, text, timeout, is_done, is_cancel, notify_format, **kwargs
        )
