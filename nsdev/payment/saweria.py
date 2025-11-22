import httpx
from ..data.ymlreder import YamlHandler

class SaweriaApi:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.maelyn.sbs/api/saweria"
        self.convert = YamlHandler()

    async def get_user_id(self, username: str):
        url = f"{self.base_url}/check/user"
        headers = {"Content-Type": "application/json", "mg-apikey": self.api_key}
        payload = {"username": username.strip()}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return self.convert._convertToNamespace(response.json())
        except Exception as e:
            raise Exception(
                self.convert._convertToNamespace({"status": "error", "message": f"Failed to get user ID: {str(e)}"})
            )

    async def create_payment(self, user_id: str, amount: int, name: str, email: str, message: str = ""):
        url = f"{self.base_url}/create/payment"
        headers = {"Content-Type": "application/json", "mg-apikey": self.api_key}
        payload = {
            "user_id": user_id.strip(),
            "amount": str(amount),
            "name": name.strip(),
            "email": email.strip(),
            "msg": message.strip(),
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return self.convert._convertToNamespace(response.json())
        except Exception as e:
            raise Exception(
                self.convert._convertToNamespace({"status": "error", "message": f"Failed to create payment: {str(e)}"})
            )

    async def check_payment(self, user_id: str, payment_id: str):
        url = f"{self.base_url}/check/payment"
        headers = {"Content-Type": "application/json", "mg-apikey": self.api_key}
        payload = {"user_id": user_id.strip(), "payment_id": payment_id.strip()}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return self.convert._convertToNamespace(response.json())
        except Exception as e:
            raise Exception(
                self.convert._convertToNamespace({"status": "error", "message": f"Failed to check payment: {str(e)}"})
            )
