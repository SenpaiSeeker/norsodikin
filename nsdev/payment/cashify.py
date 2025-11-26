import random

import httpx

from ..data.ymlreder import YamlHandler


class PaymentCashify:
    def __init__(self, license_key: str):
        self.license_key = license_key
        self.base_url = "https://cashify.my.id/api"
        self.convert = YamlHandler()
        self.qr_generator_url = "https://larabert-qrgen.hf.space/v1/create-qr-code"
        self.STYLISH_QR_COLORS = [
            "ea580c",
            "3b82f6",
            "16a34a",
            "dc2626",
            "7c3aed",
            "db2777",
            "0d9488",
            "d97706",
        ]

    def _get_headers(self):
        return {"x-license-key": self.license_key, "content-type": "application/json"}

    async def generate_qris(
        self,
        qris_id: str,
        amount: int,
        use_unique_code: bool = True,
        package_ids: list = None,
        expired_in_minutes: int = 15,
    ):
        url = f"{self.base_url}/generate/qris"

        if package_ids is None:
            package_ids = ["id.dana"]

        if expired_in_minutes < 15:
            expired_in_minutes = 15
        elif expired_in_minutes > 1440:
            expired_in_minutes = 1440

        payload = {
            "id": qris_id,
            "amount": amount,
            "useUniqueCode": use_unique_code,
            "packageIds": package_ids,
            "expiredInMinutes": expired_in_minutes,
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                response = await client.post(url, headers=self._get_headers(), json=payload)
                response.raise_for_status()
                return self.convert._convertToNamespace(response.json())
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error from Cashify API: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Error communicating with Cashify API: {e}")
        except Exception as e:
            raise Exception(f"Error generating Cashify QRIS: {e}")

    async def check_status(self, payment_id: str):
        url = f"{self.base_url}/generate/check-status"
        payload = {"transactionId": payment_id}

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                response = await client.post(url, headers=self._get_headers(), json=payload)
                response.raise_for_status()
                return self.convert._convertToNamespace(response.json())
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error from Cashify API: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Error communicating with Cashify API: {e}")
        except Exception as e:
            raise Exception(f"Error checking Cashify payment status: {e}")

    def generate_stylish_qr(self, data: str, size: str = "500x500", style: int = None, color: str = None):
        style = style if style else random.choice([1, 2, 3])
        color = color if color else random.choice(self.STYLISH_QR_COLORS)
        qr_url = f"{self.qr_generator_url}?size={size}&style={style}&color={color}&data={data}"
        return qr_url

    async def download_qr_image(self, data: str, size: str = "500x500", style: int = None, color: str = None):
        qr_url = self.generate_stylish_qr(data, size, style, color)

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                response = await client.get(qr_url)
                response.raise_for_status()
                return response.content
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error downloading QR image: {e.response.status_code}")
        except httpx.RequestError as e:
            raise Exception(f"Error downloading QR image: {e}")
        except Exception as e:
            raise Exception(f"Error generating QR image: {e}")
