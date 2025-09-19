import base64
import hashlib
import hmac
import json
import time
import uuid
from types import SimpleNamespace

import httpx
import requests
import fake_useragent
from faker import Faker

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
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            return self.convert._convertToNamespace(response.json())
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error communicating with Midtrans API: {e}")
        except Exception as e:
            raise Exception(f"Error creating Midtrans transaction: {e}")

    def check_transaction(self, order_id):
        url = f"{self.core_api_base_url}/{order_id}/status"
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return self.convert._convertToNamespace(response.json())
        except requests.exceptions.RequestException as e:
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
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Error creating payment: {response.json().get('message')}")
        return self.convert._convertToNamespace(response.json())

    def check_transaction(self, reference):
        url = f"{self.base_url}/transaction/detail"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"reference": reference}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Error checking payment: {response.json().get('message')}")
        return self.convert._convertToNamespace(response.json())


class VioletMediaPayClient:
    def __init__(self, api_key: str, secret_key: str, live: bool = False):
        self.faker = Faker("id_ID")
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
        url_redirect: str = "https://domainanda.com/redirect ",
        url_callback: str = "https://domainanda.com/callback ",
    ):
        url = f"{self.base_url}/create"
        ref_kode = str(uuid.uuid4().hex)
        signature = self._generate_signature(ref_kode, amount)
        expired_time = int(time.time()) + expired
        cus_nama = self.faker.name()
        cus_email = self.faker.email()
        cus_phone = self.faker.phone_number()
        payload = {
            "api_key": self.api_key,
            "secret_key": self.secret_key,
            "channel_payment": channel_payment,
            "ref_kode": ref_kode,
            "nominal": amount,
            "cus_nama": cus_nama,
            "cus_email": cus_email,
            "cus_phone": cus_phone,
            "produk": produk,
            "url_redirect": url_redirect,
            "url_callback": url_callback,
            "expired_time": expired_time,
            "signature": signature,
        }
        try:
            async with httpx.AsyncClient(verify=True, timeout=30.0) as client:
                response = await client.post(url, data=payload)
                response.raise_for_status()
                return self.convert._convertToNamespace(response.json())
        except httpx.ConnectTimeout as e:
            raise Exception(f"Connection timeout: Gagal terhubung ke server. Periksa koneksi internet Anda. Error: {e}")
        except httpx.ReadTimeout as e:
            raise Exception(f"Read timeout: Server tidak merespons dalam waktu yang ditentukan. Error: {e}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP Error: {e.response.status_code} - Server merespons dengan error: {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Network error: Terjadi kesalahan jaringan yang tidak terduga. Error: {e}")
        except Exception as e:
            raise Exception(f"Error creating payment: Terjadi kesalahan tidak terduga: {str(e)}")

    async def check_transaction(self, ref: str, ref_id: str):
        url = f"{self.base_url}/transactions"
        payload = {"api_key": self.api_key, "secret_key": self.secret_key, "ref": ref, "ref_id": ref_id}
        try:
            async with httpx.AsyncClient(verify=True, timeout=30.0) as client:
                response = await client.post(url, data=payload)
                response.raise_for_status()
                return self.convert._convertToNamespace(response.json())
        except httpx.ConnectTimeout as e:
            raise Exception(f"Connection timeout: Gagal terhubung ke server. Periksa koneksi internet Anda. Error: {e}")
        except httpx.ReadTimeout as e:
            raise Exception(f"Read timeout: Server tidak merespons dalam waktu yang ditentukan. Error: {e}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP Error: {e.response.status_code} - Server merespons dengan error: {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Network error: Terjadi kesalahan jaringan yang tidak terduga. Error: {e}")
        except Exception as e:
            raise Exception(f"Error checking transaction: Terjadi kesalahan tidak terduga: {str(e)}")


class PaymentTrakteer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.trakteer.id/v1"
        self.headers = {
            "Accept": "application/json",
            "key": self.api_key,
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": fake_useragent.UserAgent().random,
        }
        self.convert = YamlHandler()

    async def create_payment_link(
        self, amount: int, message: str, name: str = "Donatur", email: str = "donatur@anonymous.com"
    ) -> SimpleNamespace:
        url = f"{self.base_url}/payment_link"
        payload = {"price": amount, "message": message, "name": name, "email": email}
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                return self.convert._convertToNamespace(response.json())
            except httpx.HTTPStatusError as e:
                try:
                    error_details = e.response.json().get("message", e.response.text)
                except json.JSONDecodeError:
                    error_details = e.response.text
                raise Exception(f"API Trakteer Error: {e.response.status_code} - {error_details}")
            except Exception as e:
                raise Exception(f"Gagal membuat link pembayaran Trakteer: {e}")

    async def get_transaction_by_id(self, transaction_id: str) -> SimpleNamespace:
        url = f"{self.base_url}/transaction/{transaction_id}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return self.convert._convertToNamespace(response.json())
            except httpx.HTTPStatusError as e:
                try:
                    error_details = e.response.json().get("message", e.response.text)
                except json.JSONDecodeError:
                    error_details = e.response.text
                raise Exception(f"API Trakteer Error: {e.response.status_code} - {error_details}")
            except Exception as e:
                raise Exception(f"Gagal memeriksa transaksi Trakteer: {e}")
