import hashlib
import hmac
import random
import time
import uuid
import httpx
from ..data.ymlreder import YamlHandler

class VioletMediaPayClient:
    def __init__(self, api_key: str, secret_key: str, live: bool = False):
        self.convert = YamlHandler()
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://violetmediapay.com/api/live" if live else "https://violetmediapay.com/api/sanbox"

    def _generate_signature(self, ref_kode: str, amount: str) -> str:
        message = f"{ref_kode}{self.api_key}{amount}"
        signature = hmac.new(self.secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()
        return signature

    async def create_payment(
        self,
        channel_payment: str = "QRIS",
        amount: str = "1000",
        produk: str = "payment_bot",
        expired: int = 900,
        url_redirect: str = "https://example.com/redirect",
        url_callback: str = "https://example.com/callback",
    ):
        url = f"{self.base_url}/create"
        ref_kode = str(uuid.uuid4().hex)
        signature = self._generate_signature(ref_kode, amount)
        expired_time = int(time.time()) + expired

        random_id = str(random.randint(1000, 9999))
        payload = {
            "api_key": self.api_key,
            "secret_key": self.secret_key,
            "channel_payment": channel_payment,
            "ref_kode": ref_kode,
            "nominal": amount,
            "cus_nama": f"User {random_id}",
            "cus_email": f"user{random_id}@example.com",
            "cus_phone": f"0812{str(random.randint(10000000, 99999999))}",
            "produk": produk,
            "url_redirect": url_redirect,
            "url_callback": url_callback,
            "expired_time": expired_time,
            "signature": signature,
        }
        try:
            async with httpx.AsyncClient(verify=True, timeout=httpx.Timeout(30.0)) as client:
                response = await client.post(url, data=payload)
                response.raise_for_status()
                return self.convert._convertToNamespace(response.json())
        except Exception as e:
            raise Exception(f"Error creating VioletMediaPay payment: {e}")

    async def check_transaction(self, ref: str, ref_id: str):
        url = f"{self.base_url}/transactions"
        payload = {"api_key": self.api_key, "secret_key": self.secret_key, "ref": ref, "ref_id": ref_id}
        try:
            async with httpx.AsyncClient(verify=True, timeout=httpx.Timeout(30.0)) as client:
                response = await client.post(url, data=payload)
                response.raise_for_status()
                return self.convert._convertToNamespace(response.json())
        except Exception as e:
            raise Exception(f"Error checking VioletMediaPay transaction: {e}")
