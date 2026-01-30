import asyncio
from functools import wraps
from typing import List, Tuple

from pyrogram.types import Message

from ..data.database import DataBase
from ..utils.logger import LoggerHandler


class AnalyticsManager:
    def __init__(self, database: DataBase, db_id: str = "global_analytics"):
        self.db = database
        self.db_id = db_id
        self.log = LoggerHandler()

    def track_usage(self, func):
        @wraps(func)
        async def wrapped(client, message, *args, **kwargs):
            try:
                result = await func(client, message, *args, **kwargs)
            except Exception as e:
                raise e

            if isinstance(message, Message):
                asyncio.create_task(self._increment_stats(message))

            return result

        return wrapped

    async def _increment_stats(self, message: Message):
        try:
            command = None
            if hasattr(message, "command") and message.command:
                command = message.command[0]

            if not command and (message.text or message.caption):
                text = message.text or message.caption
                first_word = text.split()[0]
                if not first_word[0].isalnum():
                    command = first_word[1:]
                else:
                    command = first_word

            if not command:
                return

            command = command.lower()

            if message.from_user:
                user_id = str(message.from_user.id)
            elif message.sender_chat:
                user_id = str(message.sender_chat.id)
            else:
                user_id = str(message.chat.id)

            cmd_stats = await self.db.getVars(self.db_id, "command_usage_stats", var_key="analytics") or {}

            if not isinstance(cmd_stats, dict):
                cmd_stats = {}

            current_cmd_count = int(cmd_stats.get(command, 0))
            cmd_stats[command] = current_cmd_count + 1
            await self.db.setVars(self.db_id, "command_usage_stats", cmd_stats, var_key="analytics")

            user_stats = await self.db.getVars(self.db_id, "user_activity_stats", var_key="analytics") or {}

            if not isinstance(user_stats, dict):
                user_stats = {}

            current_user_count = int(user_stats.get(user_id, 0))
            user_stats[user_id] = current_user_count + 1
            await self.db.setVars(self.db_id, "user_activity_stats", user_stats, var_key="analytics")

        except Exception as e:
            self.log.error(f"Gagal menyimpan statistik: {e}")

    async def get_top_commands(self, limit: int = 10) -> List[Tuple[str, int]]:
        stats = await self.db.getVars(self.db_id, "command_usage_stats", var_key="analytics") or {}
        if not stats or not isinstance(stats, dict):
            return []

        clean_stats = {k: int(v) for k, v in stats.items()}
        sorted_cmds = sorted(clean_stats.items(), key=lambda item: item[1], reverse=True)
        return sorted_cmds[:limit]

    async def get_active_users(self, limit: int = 10) -> List[Tuple[int, int]]:
        stats = await self.db.getVars(self.db_id, "user_activity_stats", var_key="analytics") or {}
        if not stats or not isinstance(stats, dict):
            return []

        clean_stats = {k: int(v) for k, v in stats.items()}
        sorted_users = sorted(clean_stats.items(), key=lambda item: item[1], reverse=True)

        result = []
        for user_id_str, count in sorted_users[:limit]:
            try:
                result.append((int(user_id_str), count))
            except ValueError:
                continue

        return result

    async def get_total_usage(self) -> int:
        stats = await self.db.getVars(self.db_id, "command_usage_stats", var_key="analytics") or {}
        if not stats or not isinstance(stats, dict):
            return 0
        return sum(int(v) for v in stats.values())
