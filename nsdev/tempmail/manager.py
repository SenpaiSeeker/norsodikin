import json
import os
from typing import Any, Dict, List, Optional

from .generator import EmailGenerator
from .inbox_checker import InboxChecker
from .utils import TempMailUtils


class TempMailManager:
    def __init__(self, storage_file: str = "data/temp_mails.json"):
        self.storage_file = storage_file
        self.generator = EmailGenerator()
        self.checker = InboxChecker()
        self.utils = TempMailUtils()

        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)

        if not os.path.exists(self.storage_file):
            self._save_data({})

    def _load_data(self) -> Dict[str, Any]:
        try:
            with open(self.storage_file, "r") as f:
                return json.load(f)
        except:
            return {}

    def _save_data(self, data: Dict[str, Any]):
        with open(self.storage_file, "w") as f:
            json.dump(data, f, indent=2)

    async def create_temp_email(self, user_id: int) -> Optional[Dict[str, str]]:
        account = await self.generator.create_account()

        if account:
            data = self._load_data()

            user_key = str(user_id)
            if user_key not in data:
                data[user_key] = {"emails": []}

            email_data = {
                "email": account["email"],
                "password": account["password"],
                "token": account["token"],
                "id": account["id"],
                "created_at": TempMailUtils.format_datetime(__import__("datetime").datetime.now().isoformat()),
            }

            data[user_key]["emails"].append(email_data)
            data[user_key]["last_email"] = account["email"]

            self._save_data(data)

            return {"email": account["email"], "password": account["password"], "created_at": email_data["created_at"]}

        return None

    async def get_inbox(self, email: str, user_id: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        data = self._load_data()

        token = None
        for uid, user_data in data.items():
            if user_id and str(user_id) != uid:
                continue

            for email_data in user_data.get("emails", []):
                if email_data["email"] == email:
                    token = email_data["token"]
                    break

            if token:
                break

        if not token:
            return None

        messages = await self.checker.get_messages(token)
        return messages

    async def get_message_detail(
        self, email: str, message_id: str, user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        data = self._load_data()

        token = None
        for uid, user_data in data.items():
            if user_id and str(user_id) != uid:
                continue

            for email_data in user_data.get("emails", []):
                if email_data["email"] == email:
                    token = email_data["token"]
                    break

            if token:
                break

        if not token:
            return None

        message = await self.checker.get_message_detail(token, message_id)

        if message:
            text_content = message.get("text", "")
            html_content = " ".join(message.get("html", []))
            full_content = f"{text_content} {self.utils.clean_html(html_content)}"

            otp = self.utils.extract_otp(full_content)
            all_codes = self.utils.extract_all_codes(full_content)

            message["otp"] = otp
            message["all_codes"] = all_codes
            message["is_verification"] = self.utils.is_verification_email(message.get("subject", ""), full_content)

        return message

    async def get_last_email(self, user_id: int) -> Optional[str]:
        data = self._load_data()
        user_key = str(user_id)

        if user_key in data:
            return data[user_key].get("last_email")

        return None

    async def get_user_emails(self, user_id: int) -> List[Dict[str, str]]:
        data = self._load_data()
        user_key = str(user_id)

        if user_key in data:
            emails = data[user_key].get("emails", [])
            return [{"email": e["email"], "created_at": e["created_at"]} for e in emails]

        return []

    async def delete_email(self, user_id: int, email: str) -> bool:
        data = self._load_data()
        user_key = str(user_id)

        if user_key in data:
            emails = data[user_key].get("emails", [])
            data[user_key]["emails"] = [e for e in emails if e["email"] != email]

            if data[user_key].get("last_email") == email:
                remaining = data[user_key]["emails"]
                data[user_key]["last_email"] = remaining[-1]["email"] if remaining else None

            self._save_data(data)
            return True

        return False

    async def close(self):
        await self.generator.close()
        await self.checker.close()
