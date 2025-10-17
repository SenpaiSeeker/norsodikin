import base64
import hashlib
import hmac
import random
import time
import uuid
from typing import Dict

import httpx

from ..data.ymlreder import YamlHandler


class PaymentMidtrans:
    def __init__(
        self,
        server_key,
        client_key,
        callback_url="https://SenpaiSeeker.github.io/payment",
        is_production=True,
    ):
        self.convert = YamlHandler()
        self.server_key = server_key
        self.callback_url = callback_url
        if is_production:
            self.snap_base_url = "https://app.midtrans.com/snap/v1"
            self.core_api_base_url = "https://api.midtrans.com/v2"
        else:
            self.snap_base_url = "https://app.sandbox.midtrans.com/snap/v1"
            self.core_api_base_url = "https://api.sandbox.midtrans.com/v2"
        auth_string = f"{self.server_key}:".encode("utf-8")
        encoded_auth = base64.b64encode(auth_string).decode("utf-8")
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {encoded_auth}",
        }

    def create_payment(self, order_id, gross_amount):
        url = f"{self.snap_base_url}/transactions"
        payload = {
            "transaction_details": {"order_id": order_id, "gross_amount": gross_amount},
            "enabled_payments": ["other_qris"],
            "callbacks": {"finish": self.callback_url},
        }
        try:
            response = httpx.post(url, headers=self.headers, json=payload, timeout=httpx.Timeout(30.0))
            response.raise_for_status()
            return self.convert._convertToNamespace(response.json())
        except httpx.RequestError as e:
            raise Exception(f"Error communicating with Midtrans API: {e}")
        except Exception as e:
            raise Exception(f"Error creating Midtrans transaction: {e}")

    def check_transaction(self, order_id):
        url = f"{self.core_api_base_url}/{order_id}/status"
        try:
            response = httpx.get(url, headers=self.headers, timeout=httpx.Timeout(30.0))
            response.raise_for_status()
            return self.convert._convertToNamespace(response.json())
        except httpx.RequestError as e:
            raise Exception(f"Error communicating with Midtrans API: {e}")
        except Exception as e:
            raise Exception(f"Error checking Midtrans transaction status: {e}")


class PaymentTripay:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://tripay.co.id/api"
        self.convert = YamlHandler()

    def create_payment(self, method, amount, order_id, customer_name):
        url = f"{self.base_url}/transaction/create"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "method": method,
            "merchant_ref": order_id,
            "amount": amount,
            "customer_name": customer_name,
        }
        response = httpx.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return self.convert._convertToNamespace(response.json())

    def check_transaction(self, reference):
        url = f"{self.base_url}/transaction/detail"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"reference": reference}
        response = httpx.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return self.convert._convertToNamespace(response.json())


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


class SaweriaApi:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.maelyn.sbs/api/saweria"
        self.convert = YamlHandler()

    async def get_user_id(self, username: str):
        url = f"{self.base_url}/check/user"
        headers = {"Content-Type": "application/json", "mg-apikey": self.api_key}
        payload = {'username': username.strip()}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return self.convert._convertToNamespace(response.json())
        except Exception as e:
            return self.convert._convertToNamespace({
                "status": "error",
                "message": f"Failed to get user ID: {str(e)}"
            })

    async def create_payment(
        self, 
        user_id: str, 
        amount: int, 
        name: str, 
        email: str, 
        message: str = ""
    ):
        url = f"{self.base_url}/create/payment"
        headers = {"Content-Type": "application/json", "mg-apikey": self.api_key}
        payload = {
            'user_id': user_id.strip(),
            'amount': str(amount),
            'name': name.strip(),
            'email': email.strip(),
            'msg': message.strip()
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return self.convert._convertToNamespace(response.json())
        except Exception as e:
            return self.convert._convertToNamespace({
                "status": "error",
                "message": f"Failed to create payment: {str(e)}"
            })

    async def check_payment(self, user_id: str, payment_id: str):
        url = f"{self.base_url}/check/payment"
        headers = {"Content-Type": "application/json", "mg-apikey": self.api_key}
        payload = {
            'user_id': user_id.strip(),
            'payment_id': payment_id.strip()
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return self.convert._convertToNamespace(response.json())
        except Exception as e:
            return self.convert._convertToNamespace({
                "status": "error",
                "message": f"Failed to check payment: {str(e)}"
            })
