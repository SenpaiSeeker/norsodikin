from functools import wraps
from typing import List, Union

from pyrogram.types import CallbackQuery, Message

from ..data.database import DataBase


class AuthManager:
    def __init__(self, database: DataBase, var_key: str = "auth_roles"):
        self.db = database
        self.var_key = var_key

    async def set_role(self, user_id: int, role: str) -> None:
        self.db.setListVars(user_id, "roles", role.lower(), var_key=self.var_key)

    async def remove_role(self, user_id: int, role: str) -> None:
        self.db.removeListVars(user_id, "roles", role.lower(), var_key=self.var_key)

    async def get_roles(self, user_id: int) -> List[str]:
        return self.db.getListVars(user_id, "roles", var_key=self.var_key)

    def requires_role(self, required_roles: Union[str, List[str]]):
        if isinstance(required_roles, str):
            required_roles = [required_roles]

        required_set = {role.lower() for role in required_roles}

        def decorator(func):
            @wraps(func)
            async def wrapped(client, update, *args, **kwargs):
                if not isinstance(update, (Message, CallbackQuery)):
                    return await func(client, update, *args, **kwargs)

                user_id = update.from_user.id
                user_roles = await self.get_roles(user_id)
                user_roles_set = {role.lower() for role in user_roles}

                if not required_set.intersection(user_roles_set):
                    error_msg = "🚫 Anda tidak memiliki izin untuk menggunakan perintah ini."
                    if isinstance(update, Message):
                        await update.reply_text(error_msg)
                    elif isinstance(update, CallbackQuery):
                        await update.answer(error_msg, show_alert=True)
                    return

                return await func(client, update, *args, **kwargs)

            return wrapped

        return decorator
