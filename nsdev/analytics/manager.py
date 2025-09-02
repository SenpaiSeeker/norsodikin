import asyncio
import time
from collections import Counter
from functools import wraps
from typing import List, Tuple

from pyrogram.types import Message

from ..data.database import DataBase


class AnalyticsManager:
    def __init__(self, database: DataBase, db_id: str = "global_analytics", var_key: str = "bot_usage_stats"):
        self.db = database
        self.db_id = db_id
        self.var_key = var_key

    def track_usage(self, func):
        @wraps(func)
        async def wrapped(client, message, *args, **kwargs):
            if isinstance(message, Message) and message.command:
                log_entry = {
                    "command": message.command[0],
                    "user_id": message.from_user.id,
                    "timestamp": int(time.time()),
                }
                self.db.setListVars(self.db_id, "logs", log_entry, var_key=self.var_key)
            return await func(client, message, *args, **kwargs)

        return wrapped

    def _get_usage_logs(self) -> List[dict]:
        return self.db.getListVars(self.db_id, "logs", self.var_key)

    async def get_all_logs(self) -> List[dict]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._get_usage_logs)

    async def get_top_commands(self, limit: int = 10) -> List[Tuple[str, int]]:
        logs = await self.get_all_logs()
        if not logs:
            return []

        command_counts = Counter(log["command"] for log in logs if "command" in log)
        return command_counts.most_common(limit)

    async def get_active_users(self, limit: int = 10) -> List[Tuple[int, int]]:
        logs = await self.get_all_logs()
        if not logs:
            return []

        user_counts = Counter(log["user_id"] for log in logs if "user_id" in log)
        return user_counts.most_common(limit)
