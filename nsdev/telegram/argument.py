import asyncio
from datetime import datetime
from typing import Optional, Tuple, Union

import pyrogram


class Argument:
    def __init__(self, client):
        self.client: pyrogram.Client = client

    def getMention(
        self,
        user: pyrogram.types.User,
        logs: bool = False,
        no_tag: bool = False,
        tag_and_id: bool = False,
    ) -> str:
        
        name = user.first_name
        if user.last_name:
            name += f" {user.last_name}"

        if logs:
            return f"{name} ({user.id})"
        if no_tag:
            return name
            
        link = f"tg://user?id={user.id}"
        mention = f"<a href='{link}'>{name}</a>"
        if tag_and_id:
            mention += f" | <code>{user.id}</code>"
        
        return mention

    async def getNamebot(self, bot_token: str) -> str:
        temp_bot_client = pyrogram.Client(
            name="temp_bot_name_fetcher",
            api_id=self.client.api_id,
            api_hash=self.client.api_hash,
            bot_token=bot_token,
            in_memory=True
        )
        try:
            async with temp_bot_client:
                me = await temp_bot_client.get_me()
                return me.first_name
        except Exception:
            return "Bot token invalid"

    def getMessage(
        self,
        message: pyrogram.types.Message,
        is_arg: bool = False,
        is_tuple: bool = False,
    ) -> Union[str, pyrogram.types.Message, Tuple[Optional[str], Optional[str]]]:
        
        text_content = message.text or message.caption or ""
        command_parts = message.command or text_content.split()
        replied = message.reply_to_message

        replied_text = ""
        if replied:
            replied_text = replied.text or replied.caption or ""
        
        quote_text = ""
        if hasattr(message, "quote") and message.quote:
             quote_text = message.quote.text or ""

        if is_tuple:
            part1 = command_parts[1] if len(command_parts) > 1 else None
            part2 = " ".join(command_parts[2:]) if len(command_parts) > 2 else (replied_text or quote_text or None)
            return part1, part2

        if is_arg:
            if len(command_parts) > 1:
                return text_content.split(None, 1)[1]
            if replied and replied_text:
                return replied_text
            if quote_text:
                return quote_text
            return ""

        if replied:
            return replied
        if len(command_parts) > 1:
            return text_content.split(None, 1)[1]
        
        return ""

    async def getReasonAndId(
        self, message: pyrogram.types.Message, sender_chat: bool = False
    ) -> Tuple[Optional[int], Optional[str]]:
        
        args = (message.text or "").strip().split()
        replied = message.reply_to_message
        target_id = None
        reason = None
        
        if replied:
            if replied.from_user:
                target_id = replied.from_user.id
            elif sender_chat and replied.sender_chat:
                target_id = replied.sender_chat.id
            
            if len(args) > 1:
                reason = " ".join(args[1:])
        
        elif len(args) > 1:
            try:
                target_user = await self.client.get_users(args[1])
                target_id = target_user.id
                if len(args) > 2:
                    reason = " ".join(args[2:])
            except Exception:
                return None, None
        
        return target_id, reason

    async def getAdmin(self, message: pyrogram.types.Message) -> bool:
        try:
            member = await self.client.get_chat_member(message.chat.id, message.from_user.id)
            return member.status in (
                pyrogram.enums.ChatMemberStatus.ADMINISTRATOR,
                pyrogram.enums.ChatMemberStatus.OWNER,
            )
        except Exception:
            return False

    async def getId(self, message: pyrogram.types.Message) -> Optional[int]:
        user_id, _ = await self.getReasonAndId(message, sender_chat=True)
        return user_id

    async def copyMessage(self, chatId: int, msgId: int, chatTarget: int):
        try:
            await self.client.copy_message(chatTarget, chatId, msgId)
            await asyncio.sleep(1)
        except Exception:
            pass

    async def ping(self) -> float:
        start = datetime.now()
        await self.client.invoke(pyrogram.raw.functions.Ping(ping_id=0))
        end = datetime.now()
        delta_ping = (end - start).microseconds / 1000
        return delta_ping
