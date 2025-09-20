import asyncio
from types import SimpleNamespace
from dataclasses import dataclass
from enum import Enum
from inspect import iscoroutinefunction
from typing import Callable, Optional, Dict, List, Union, Tuple

import pyrogram
from pyrogram.filters import Filter
from pyrogram.types import CallbackQuery, Message

config = SimpleNamespace(
    timeout_handler=None,
    stopped_handler=None,
    throw_exceptions=True,
    unallowed_click_alert=True,
    unallowed_click_alert_text="[nsdev] Anda tidak diizinkan menekan tombol ini.",
    disable_startup_logs=False,
)

class ListenerTimeout(Exception):
    pass

class ListenerStopped(Exception):
    pass

pyrogram.errors.ListenerTimeout = ListenerTimeout
pyrogram.errors.ListenerStopped = ListenerStopped

class ListenerTypes(Enum):
    MESSAGE = "message"
    CALLBACK_QUERY = "callback_query"

@dataclass
class Identifier:
    inline_message_id: Optional[Union[str, List[str]]] = None
    chat_id: Optional[Union[Union[int, str], List[Union[int, str]]]] = None
    message_id: Optional[Union[int, List[int]]] = None
    from_user_id: Optional[Union[Union[int, str], List[Union[int, str]]]] = None

    def matches(self, update: "Identifier") -> bool:
        for field in self.__annotations__:
            pattern_value = getattr(self, field)
            update_value = getattr(update, field)
            if pattern_value is not None:
                pattern_list = pattern_value if isinstance(pattern_value, list) else [pattern_value]
                update_list = update_value if isinstance(update_value, list) else [update_value]
                if not any(item in pattern_list for item in update_list if item is not None):
                    return False
        return True

    def count_populated(self):
        return sum(1 for field in self.__annotations__ if getattr(self, field) is not None)

@dataclass
class Listener:
    listener_type: ListenerTypes
    filters: Filter
    unallowed_click_alert: bool
    identifier: Identifier
    future: asyncio.Future = None
    callback: Callable = None

def patch_into(target_class):
    def is_patchable(item):
        return hasattr(item[1], "should_patch")

    def wrapper(container):
        for name, func in filter(is_patchable, container.__dict__.items()):
            old = getattr(target_class, name, None)
            if old is not None:
                setattr(target_class, "old" + name, old)
            setattr(target_class, name, func)
        return container
    return wrapper

def should_patch(func):
    func.should_patch = True
    return func


@patch_into(pyrogram.Client)
class Client:
    @should_patch
    def __init__(self, *args, **kwargs):
        self.listeners: Dict[ListenerTypes, List[Listener]] = {
            t: [] for t in ListenerTypes
        }
        if hasattr(self, 'old__init__'):
            self.old__init__(*args, **kwargs)
        else:
            super(pyrogram.Client, self).__init__(*args, **kwargs)
            
        if not config.disable_startup_logs:
            print("[nsdev.listen] Fitur percakapan interaktif (pyromod) berhasil diaktifkan.")

    @should_patch
    async def listen(
        self,
        filters: Optional[Filter] = None,
        listener_type: ListenerTypes = ListenerTypes.MESSAGE,
        timeout: Optional[int] = None,
        unallowed_click_alert: bool = True,
        chat_id: Union[int, str, List[Union[int, str]]] = None,
        user_id: Union[int, str, List[Union[int, str]]] = None,
        message_id: Union[int, List[int]] = None,
        inline_message_id: Union[str, List[str]] = None,
    ):
        pattern = Identifier(
            from_user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )
        future = asyncio.get_event_loop().create_future()
        listener = Listener(future, filters, unallowed_click_alert, pattern, listener_type)
        future.add_done_callback(lambda _f: self.remove_listener(listener))
        self.listeners[listener_type].append(listener)
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            if callable(config.timeout_handler):
                await config.timeout_handler(pattern, listener, timeout)
            elif config.throw_exceptions:
                raise ListenerTimeout(f"Listener timed out after {timeout} seconds.") from None

    @should_patch
    async def ask(
        self,
        chat_id: Union[int, str],
        text: str,
        filters: Optional[Filter] = None,
        timeout: Optional[int] = None,
        *args, **kwargs
    ):
        sent_message = None
        if text and text.strip():
            sent_message = await self.send_message(chat_id, text, *args, **kwargs)
        
        response = await self.listen(
            filters=filters,
            timeout=timeout,
            chat_id=chat_id,
            user_id=kwargs.get("user_id"),
        )
        
        if response:
            response.request = sent_message
        return response

    @should_patch
    def remove_listener(self, listener: Listener):
        try:
            self.listeners[listener.listener_type].remove(listener)
        except ValueError:
            pass

    @should_patch
    def get_listener_matching_with_data(
        self, data: Identifier, listener_type: ListenerTypes
    ) -> Optional[Listener]:
        matching = [
            l for l in self.listeners[listener_type] if l.identifier.matches(data)
        ]
        return max(matching, key=lambda l: l.identifier.count_populated(), default=None)

@patch_into(pyrogram.handlers.MessageHandler)
class MessageHandler:
    @should_patch
    def __init__(self, callback: Callable, filters: Filter = None):
        self.original_callback = callback
        self.old__init__(self._resolver, filters)
        
    async def _check_and_get_listener(self, client: Client, message: Message) -> Tuple[bool, Listener]:
        from_user = message.from_user
        data = Identifier(
            message_id=message.id,
            chat_id=[message.chat.id, message.chat.username] if message.chat else None,
            from_user_id=[from_user.id, from_user.username] if from_user else None
        )
        
        listener = client.get_listener_matching_with_data(data, ListenerTypes.MESSAGE)
        if not listener:
            return False, None
            
        filters = listener.filters
        if not callable(filters):
            return True, listener

        if iscoroutinefunction(filters.__call__):
            return await filters(client, message), listener
        return await client.loop.run_in_executor(None, filters, client, message), listener

    @should_patch
    async def check(self, client: Client, message: Message):
        listener_does_match, _ = await self._check_and_get_listener(client, message)
        
        if callable(self.filters):
            if iscoroutinefunction(self.filters.__call__):
                handler_does_match = await self.filters(client, message)
            else:
                handler_does_match = await client.loop.run_in_executor(None, self.filters, client, message)
        else:
            handler_does_match = True

        return listener_does_match or handler_does_match

    @should_patch
    async def _resolver(self, client: Client, message: Message, *args):
        listener_does_match, listener = await self._check_and_get_listener(client, message)

        if listener and listener_does_match:
            client.remove_listener(listener)
            if listener.future and not listener.future.done():
                listener.future.set_result(message)
                raise pyrogram.StopPropagation
        else:
            await self.original_callback(client, message, *args)

@patch_into(pyrogram.handlers.CallbackQueryHandler)
class CallbackQueryHandler:
    @should_patch
    def __init__(self, callback: Callable, filters: Filter = None):
        self.original_callback = callback
        self.old__init__(self._resolver, filters)

    def _compose_data_identifier(self, query: CallbackQuery):
        from_user = query.from_user
        chat = query.message.chat if query.message else None
        return Identifier(
            inline_message_id=query.inline_message_id,
            chat_id=[chat.id, chat.username] if chat else None,
            message_id=query.message.id if query.message else None,
            from_user_id=[from_user.id, from_user.username] if from_user else None,
        )

    async def _check_and_get_listener(self, client: Client, query: CallbackQuery) -> Tuple[bool, Listener]:
        data = self._compose_data_identifier(query)
        listener = client.get_listener_matching_with_data(data, ListenerTypes.CALLBACK_QUERY)
        if not listener:
            return False, None
            
        filters = listener.filters
        if not callable(filters):
            return True, listener

        if iscoroutinefunction(filters.__call__):
            return await filters(client, query), listener
        return await client.loop.run_in_executor(None, filters, client, query), listener

    @should_patch
    async def check(self, client: Client, query: CallbackQuery):
        listener_does_match, listener = await self._check_and_get_listener(client, query)
        
        if callable(self.filters):
            if iscoroutinefunction(self.filters.__call__):
                handler_does_match = await self.filters(client, query)
            else:
                handler_does_match = await client.loop.run_in_executor(None, self.filters, client, query)
        else:
            handler_does_match = True

        data = self._compose_data_identifier(query)
        if config.unallowed_click_alert and listener and listener.unallowed_click_alert:
            permissive_identifier = Identifier(
                chat_id=data.chat_id,
                message_id=data.message_id,
                inline_message_id=data.inline_message_id
            )
            if permissive_identifier.matches(data) and not listener_does_match:
                alert = listener.unallowed_click_alert if isinstance(listener.unallowed_click_alert, str) else config.unallowed_click_alert_text
                await query.answer(alert, show_alert=True)
                return False

        return listener_does_match or handler_does_match

    @should_patch
    async def _resolver(self, client: Client, query: CallbackQuery, *args):
        listener_does_match, listener = await self._check_and_get_listener(client, query)

        if listener and listener_does_match:
            client.remove_listener(listener)
            if listener.future and not listener.future.done():
                listener.future.set_result(query)
                raise pyrogram.StopPropagation
        else:
            await self.original_callback(client, query, *args)


@patch_into(pyrogram.types.Chat)
class PatchedChat:
    @should_patch
    def listen(self, *args, **kwargs):
        return self._client.listen(*args, chat_id=self.id, **kwargs)

    @should_patch
    def ask(self, text, *args, **kwargs):
        return self._client.ask(self.id, text, *args, **kwargs)

@patch_into(pyrogram.types.User)
class PatchedUser:
    @should_patch
    def listen(self, *args, **kwargs):
        return self._client.listen(*args, user_id=self.id, **kwargs)

    @should_patch
    def ask(self, text, *args, **kwargs):
        return self._client.ask(self.id, text, *args, user_id=self.id, **kwargs)
