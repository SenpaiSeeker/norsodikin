import asyncio
import io
import json
import re
import time
from typing import Optional, Tuple
import cloudscraper25 as cloudscraper
from bs4 import BeautifulSoup
from ..ai.qrcode import QrCodeGenerator

class SaweriaScraper(QrCodeGenerator):
    BACKEND = "https://backend.saweria.co"
    FRONTEND = "https://saweria.co"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://saweria.co/",
    }

    def __init__(self):
        super().__init__()
        self.scraper = cloudscraper.create_scraper()

    async def get_user_id(self, username: str) -> Optional[str]:
        if not username or not isinstance(username, str):
            raise ValueError("Username harus berupa string dan tidak boleh kosong.")

        def _sync_get_with_retries(retries=3, delay=5):
            url = f"{self.FRONTEND}/{username}"
            for attempt in range(retries):
                try:
                    res = self.scraper.get(url, headers=self.HEADERS, timeout=15)
                    if res.status_code == 200:
                        soup = BeautifulSoup(res.text, "html.parser")
                        next_data = soup.find(id="__NEXT_DATA__")
                        if next_data:
                            data = json.loads(next_data.text)
                            user_id = data.get("props", {}).get("pageProps", {}).get("data", {}).get("id")
                            if user_id:
                                return user_id
                except Exception:
                    pass
                time.sleep(delay)
            return None

        return await asyncio.to_thread(_sync_get_with_retries)

    async def create_payment(
        self,
        user_id: str,
        amount: int,
        name: str,
        email: str,
        message: str,
        creator_name: str = "nsdev",
    ) -> Tuple[str, str, io.BytesIO, int]:
        if amount < 1000:
            raise ValueError("Jumlah minimum donasi adalah 1000")

        payload = {
            "agree": True,
            "notUnderage": True,
            "message": message,
            "amount": amount,
            "payment_type": "qris",
            "vote": "",
            "currency": "IDR",
            "customer_info": {"first_name": name, "email": email, "phone": ""},
        }

        def _sync_post():
            res = self.scraper.post(
                f"{self.BACKEND}/donations/{user_id}",
                json=payload,
                headers=self.HEADERS,
            )
            if not res.ok:
                raise Exception(f"Gagal membuat pembayaran: {res.text}")
            return res.json()["data"]

        data = await asyncio.to_thread(_sync_post)
        qr_string = data["qr_string"]
        transaction_id = data["id"]
        amount_raw = data["amount_raw"]

        qr_image_bytes = await self.generate(
            data=qr_string,
            use_dots=True,
            glow_background=False,
            bottom_text="SCAN ME",
            creator_text=f"Created by: {creator_name}",
        )

        qr_image_stream = io.BytesIO(qr_image_bytes)
        qr_image_stream.name = f"{transaction_id}.png"

        return qr_string, transaction_id, qr_image_stream, amount_raw

    async def check_paid_status(self, transaction_id: str) -> bool:
        def _sync_get():
            res = self.scraper.get(f"{self.BACKEND}/donations/qris/{transaction_id}", headers=self.HEADERS)
            if not res.ok:
                raise Exception("Transaction ID not found")
            return res.json()["data"]["qr_string"] == ""

        return await asyncio.to_thread(_sync_get)

    def get_amount(self, qr_text: str):
        match = re.search(r"54(\d{2})(\d+)", qr_text)
        if not match:
            return None
        length = int(match.group(1))
        value = match.group(2)[:length]
        try:
            return int(value)
        except ValueError:
            return None
