import base64

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
