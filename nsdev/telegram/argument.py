import asyncio
import pyrogram
import requests

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
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        try:
            response = requests.get(url)
            data = response.json()
            if data.get("ok"):
                return data["result"]["first_name"]
            return "Bot token invalid"
        except requests.exceptions.RequestException as error:
            return str(error)

    def getMessage(self, message, is_arg=False, is_tuple=False):
        if is_tuple:
            args = message.command[1:] if hasattr(message, "command") and message.command else []
            replied = message.reply_to_message
            part1 = None
            part2 = None
            
            if args:
                part1 = args[0]
                if len(args) > 1:
                    part2 = " ".join(args[1:])
                elif replied and (replied.text or replied.caption):
                    part2 = replied.text or replied.caption
            elif replied and (replied.text or replied.caption):
                part2 = replied.text or replied.caption
            
            return part1, part2
            
        if is_arg:
            if message.reply_to_message and (not hasattr(message, "command") or len(message.command) < 2):
                return message.reply_to_message.text or message.reply_to_message.caption
            elif hasattr(message, "command") and len(message.command) > 1:
                return message.text.split(None, 1)[1]
            else:
                return ""
        else:
            if message.reply_to_message:
                return message.reply_to_message
            elif hasattr(message, "command") and len(message.command) > 1:
                return message.text.split(None, 1)[1]
            else:
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
