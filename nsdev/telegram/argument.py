import asyncio

import pyrogram
import requests
from datetime import datetime 


class Argument:
    def __init__(self, client):
        self.client = client

    def getMention(self, me, logs=False, no_tag=False, tag_and_id=False):
        name = f"{me.first_name} {me.last_name}" if me.last_name else me.first_name
        link = f"tg://user?id={me.id}"
        return (
            f"{name} ({me.id})"
            if logs
            else (
                name
                if no_tag
                else f"<a href='{link}'>{name}</a>{' | <code>' + str(me.id) + '</code>' if tag_and_id else ''}"
            )
        )

    def getNamebot(self, bot_token):
        url = f"https://api.telegram.org/bot  {bot_token}/getMe"
        try:
            response = requests.get(url)
            data = response.json()
            if data.get("ok"):
                return data["result"]["first_name"]
            return "Bot token invalid"
        except requests.exceptions.RequestException as error:
            return str(error)

    def getMessage(self, message, is_arg=False, is_tuple=False):
        cmd = getattr(message, "command", []) or []
        replied = getattr(message, "reply_to_message", None)

        def _text_of(msg):
            return getattr(msg, "text", None) or getattr(msg, "caption", None) or ""

        if is_tuple:
            args = cmd[1:] if cmd else []
            part1 = args[0] if args else None
            if len(args) > 1:
                part2 = " ".join(args[1:])
            else:
                part2 = _text_of(replied) if replied else None
            return part1, part2

        if is_arg:
            if replied and len(cmd) < 2:
                return _text_of(replied)
            if len(cmd) > 1:
                rest = _text_of(message)
                return rest.split(None, 1)[1] if rest and len(rest.split(None, 1)) > 1 else ""
            return ""

        if replied:
            return replied
        if len(cmd) > 1:
            rest = _text_of(message)
            return rest.split(None, 1)[1] if rest and len(rest.split(None, 1)) > 1 else ""
        return ""

    async def getReasonAndId(self, message, sender_chat=False):
        args = message.text.strip().split()
        reply = message.reply_to_message
        user_id = None
        reason = None

        if reply:
            if reply.from_user:
                user_id = reply.from_user.id
            elif sender_chat and reply.sender_chat:
                user_id = reply.sender_chat.id

            if len(args) > 1:
                reason = " ".join(args[1:])
            return user_id, reason

        if len(args) > 1:
            try:
                user = await self.client.get_users(args[1])
                user_id = user.id
            except Exception:
                return None, None

            if len(args) > 2:
                reason = " ".join(args[2:])
            return user_id, reason

        return None, None

    async def getAdmin(self, message):
        member = await self.client.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in (
            pyrogram.enums.ChatMemberStatus.ADMINISTRATOR,
            pyrogram.enums.ChatMemberStatus.OWNER,
        )

    async def getId(self, message):
        user_id, _ = await self.getReasonAndId(message, sender_chat=True)
        return user_id

    async def copyMessage(self, chatId, msgId, chatTarget):
        get_msg = await self.client.get_messages(chatId, msgId)
        await get_msg.copy(chatTarget, protect_content=True)
        await asyncio.sleep(1)

    async def ping(self):
        start = datetime.now()
        await self.client.invoke(pyrogram.raw.functions.Ping(ping_id=0))
        end = datetime.now()
        delta_ping = (end - start).microseconds / 1000
        return delta_ping
