class Argument:
    def __init__(self):
        self.asyncio = __import__("asyncio")
        self.pyrogram = __import__("pyrogram")

    def getMessage(self, message, is_arg=False):
        return (
            (
                message.reply_to_message.text or message.reply_to_message.caption
                if message.reply_to_message and len(message.command) < 2
                else message.text.split(None, 1)[1] if len(message.command) > 1 else ""
            )
            if is_arg
            else message.reply_to_message if message.reply_to_message else message.text.split(None, 1)[1] if len(message.command) > 1 else ""
        )

    async def getUserId(self, message, username):
        if entities := message.entities:
            entity = entities[1 if message.text.startswith("/") else 0]
            return (
                (await message._client.get_chat(username)).id
                if entity.type == self.pyrogram.enums.MessageEntityType.MENTION
                else entity.user.id if entity.type == self.pyrogram.enums.MessageEntityType.TEXT_MENTION else username
            )
        return username

    async def userId(self, message, text):
        return int(text) if text.isdigit() else await self.getUserId(message, text)

    async def getReasonAndId(self, message, sender_chat=False):
        text, args, reply = message.text.strip(), message.text.split(), message.reply_to_message

        if reply:
            user_id = (reply.from_user.id if reply.from_user else reply.sender_chat.id) if sender_chat and reply.sender_chat and reply.sender_chat.id != message.chat.id else None
            return (user_id, text.split(None, 1)[1] if len(args) > 1 else None) if user_id else (None, None)

        return (await self.userId(message, args[1]), None) if len(args) == 2 else (await self.userId(message, args[1]), " ".join(args[2:])) if len(args) > 2 else (None, None)

    async def getAdmin(self, message):
        return (await message._client.get_chat_member(message.chat.id, message.from_user.id)).status in (
            self.pyrogram.enums.ChatMemberStatus.ADMINISTRATOR,
            self.pyrogram.enums.ChatMemberStatus.OWNER,
        )

    async def getId(self, message):
        return (await self.getReasonAndId(message))[0]

    async def copyMessage(self, client, chatId, msgId, chatTarget):
        get_msg = await client.get_messages(chatId, msgId)
        await get_msg.copy(chatTarget, protect_content=True)
        await self.asyncio.sleep(1)
