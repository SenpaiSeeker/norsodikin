import asyncio
from functools import wraps
from typing import List, Tuple, Dict

from pyrogram.types import Message

from ..data.database import DataBase


class AnalyticsManager:
    def __init__(self, database: DataBase, db_id: str = "global_analytics"):
        self.db = database
        self.db_id = db_id

    def track_usage(self, func):
        @wraps(func)
        async def wrapped(client, message, *args, **kwargs):
            try:
                result = await func(client, message, *args, **kwargs)
            except Exception as e:
                raise e

            if isinstance(message, Message) and message.command:
                asyncio.create_task(self._increment_stats(message))

            return result

        return wrapped

    async def _increment_stats(self, message: Message):
        try:
            command = message.command[0].lower()
            user_id = str(message.from_user.id) if message.from_user else str(message._client.me.id)

            cmd_stats = await self.db.getVars(self.db_id, "command_usage_stats") or {}
            current_cmd_count = cmd_stats.get(command, 0)
            cmd_stats[command] = current_cmd_count + 1
            await self.db.setVars(self.db_id, "command_usage_stats", cmd_stats)

            user_stats = await self.db.getVars(self.db_id, "user_activity_stats") or {}
            current_user_count = user_stats.get(user_id, 0)
            user_stats[user_id] = current_user_count + 1
            await self.db.setVars(self.db_id, "user_activity_stats", user_stats)

        except Exception:
            pass

    async def get_top_commands(self, limit: int = 10) -> List[Tuple[str, int]]:
        stats = await self.db.getVars(self.db_id, "command_usage_stats") or {}
        if not stats:
            return []

        sorted_cmds = sorted(stats.items(), key=lambda item: item[1], reverse=True)
        return sorted_cmds[:limit]

    async def get_active_users(self, limit: int = 10) -> List[Tuple[int, int]]:
        stats = await self.db.getVars(self.db_id, "user_activity_stats") or {}
        if not stats:
            return []

        sorted_users = sorted(stats.items(), key=lambda item: item[1], reverse=True)
        
        result = []
        for user_id_str, count in sorted_users[:limit]:
            try:
                result.append((int(user_id_str), count))
            except ValueError:
                continue
                
        return result

    async def get_total_usage(self) -> int:
        stats = await self.db.getVars(self.db_id, "command_usage_stats") or {}
        return sum(stats.values())
