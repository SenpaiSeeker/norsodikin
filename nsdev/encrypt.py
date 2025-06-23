import asyncio
import importlib
from time import time

from nsdev import LoggerHandler
from pyrogram import Client, handlers
from pyromod import listen

from FsubBuilderBot.config import Config
from FsubBuilderBot.Modules import modules

uptime = time()
log = LoggerHandler()


class Bot(Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bot = []

    def getmention(self, me, logs=False, no_tag=False, tag_and_id=False):
        name = f"{me.first_name} {me.last_name}" if me.last_name else me.first_name
        link = f"tg://user?id={me.id}"
        return (
            f"{me.id}|{name}"
            if logs
            else name if no_tag else f"<a href='{link}'>{name}</a>{' | <code>' + str(me.id) + '</code>' if tag_and_id else ''}"
        )

    def on_message(self, filters=None, group=-1):
        def decorator(func):
            for xb in self.bot:
                xb.add_handler(handlers.MessageHandler(func, filters), group)
            return func

        return decorator

    def on_callback_query(self, filters=None, group=-1):
        def decorator(func):
            for xb in self.bot:
                xb.add_handler(handlers.CallbackQueryHandler(func, filters), group)
            return func

        return decorator

    async def get_module(self):
        for mod in modules:
            await asyncio.sleep(0.5)
            try:
                importlib.reload(importlib.import_module(f"FsubBuilderBot.Modules.{mod}"))
                log.print(f"{log.BLUE}Module {log.WHITE}{mod} {log.GREEN}loaded successfully.")
            except Exception as e:
                log.print(f"{log.YELLOW}Failed to load module {log.WHITE}{mod}: {log.RED}{e}")
        log.print(f"{log.LIGHT_BLUE}=" * 50)

    async def start(self):
        await super().start()
        self.bot.append(self)
        text = f"{log.CYAN}[ {log.GREEN}Bot: {log.WHITE}{self.getmention(self.me, logs=True)} {log.BLUE}- {log.GREEN}Starting {log.CYAN}]"
        log.print(text)


bot = Bot(**Config.RANDOM_API, bot_token=Config.BOT_TOKEN)
from FsubBuilderBot.Core import telegram
