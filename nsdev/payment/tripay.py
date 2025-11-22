import httpx
from ..data.ymlreder import YamlHandler

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
