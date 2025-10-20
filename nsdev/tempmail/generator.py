import random
import string
from typing import Any, Dict, Optional

import aiohttp

from ..utils.logger import LoggerHandler


class EmailGenerator:
    BASE_URL = "https://api.mail.tm"

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = LoggerHandler()

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_available_domains(self) -> list:
        session = await self._get_session()
        try:
            async with session.get(f"{self.BASE_URL}/domains") as response:
                if response.status == 200:
                    data = await response.json()
                    return [domain["domain"] for domain in data["hydra:member"]]
                return []
        except Exception as e:
            error_text = f"Error getting domains: {e}"
            self.logger.error(error_text)
            raise Exception(error_text)

    def _generate_random_username(self, length: int = 10) -> str:
        chars = string.ascii_lowercase + string.digits
        return "".join(random.choice(chars) for _ in range(length))

    def _generate_random_password(self, length: int = 16) -> str:
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(random.choice(chars) for _ in range(length))

    async def create_account(self) -> Optional[Dict[str, Any]]:
        session = await self._get_session()

        domains = await self.get_available_domains()
        if not domains:
            return None

        username = self._generate_random_username()
        password = self._generate_random_password()
        domain = random.choice(domains)
        email = f"{username}@{domain}"

        try:
            account_data = {"address": email, "password": password}

            async with session.post(f"{self.BASE_URL}/accounts", json=account_data) as response:
                if response.status in [200, 201]:
                    account_info = await response.json()

                    token = await self._login(email, password)
                    if token:
                        return {"email": email, "password": password, "token": token, "id": account_info.get("id", "")}
        except Exception as e:
            error_text = f"Error creating account: {e}"
            self.logger.error(error_text)
            raise Exception(error_text)

        return None

    async def _login(self, email: str, password: str) -> Optional[str]:
        session = await self._get_session()

        try:
            login_data = {"address": email, "password": password}

            async with session.post(f"{self.BASE_URL}/token", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("token")
        except Exception as e:
            error_text = f"Error logging in: {e}"
            self.logger.error(error_text)
            raise Exception(error_text)

        return None

    async def verify_account(self, email: str, password: str) -> bool:
        token = await self._login(email, password)
        return token is not None
