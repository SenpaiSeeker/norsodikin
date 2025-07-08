class Argument:
    def __init__(self):
        self.asyncio = __import__("asyncio")
        self.pyrogram = __import__("pyrogram")
        self.requests = __import__("requests")

    def getMention(self, me, logs=False, no_tag=False, tag_and_id=False):
        name = f"{me.first_name} {me.last_name}" if me.last_name else me.first_name
        link = f"tg://user?id={me.id}"
        return (
            f"{me.id}|{name}"
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
            response = self.requests.get(url)
            data = response.json()
            if data.get("ok"):
                return data["result"]["first_name"]
            return "Bot token invalid"
        except self.requests.exceptions.RequestException as error:
            return str(error)

    def getMessage(self, message, is_arg=False):
        if is_arg:
            if message.reply_to_message and len(message.command) < 2:
                return message.reply_to_message.text or message.reply_to_message.caption
            elif len(message.command) > 1:
                return message.text.split(None, 1)[1]
            else:
                return ""
        else:
            if message.reply_to_message:
                return message.reply_to_message
            elif len(message.command) > 1:
                return message.text.split(None, 1)[1]
            else:
                return ""

    async def getUserId(self, message, username):
        if message.entities:
            entity_index = 1 if message.text.startswith("/") else 0
            entity = message.entities[entity_index]
            if entity.type == self.pyrogram.enums.MessageEntityType.MENTION:
                return (await message._client.get_chat(username)).id
            elif entity.type == self.pyrogram.enums.MessageEntityType.TEXT_MENTION:
                return entity.user.id
        return username

    async def userId(self, message, text):
        return int(text) if text.isdigit() else await self.getUserId(message, text)

    async def getReasonAndId(self, message, sender_chat=False):
        text = message.text.strip()
        args = text.split()
        reply = message.reply_to_message

        if reply:
            if reply.from_user:
                user_id = reply.from_user.id
            elif sender_chat and reply.sender_chat:
                user_id = reply.sender_chat.id
            else:
                user_id = None

            reason = text.split(None, 1)[1] if len(args) > 1 else None
            return (user_id, reason) if user_id else (None, None)

        if len(args) == 2:
            return (await self.userId(message, args[1]), None)
        elif len(args) > 2:
            return (await self.userId(message, args[1]), " ".join(args[2:]))
        else:
            return (None, None)

    async def getAdmin(self, message):
        member = await message._client.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in (
            self.pyrogram.enums.ChatMemberStatus.ADMINISTRATOR,
            self.pyrogram.enums.ChatMemberStatus.OWNER,
        )

    async def getId(self, message):
        user_id, _ = await self.getReasonAndId(message, sender_chat=True)
        return user_id

    async def copyMessage(self, client, chatId, msgId, chatTarget):
        get_msg = await client.get_messages(chatId, msgId)
        await get_msg.copy(chatTarget, protect_content=True)
        await self.asyncio.sleep(1)
