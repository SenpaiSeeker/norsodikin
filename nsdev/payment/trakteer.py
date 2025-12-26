import aiohttp
import re
import json
import uuid

class TrakteerScraper:
    def __init__(self):
        self.base_url = "https://trakteer.id"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01"
        }

    async def get_creator_data(self, username):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/{username}") as resp:
                text = await resp.text()
                
                creator_id_match = re.search(r'name="creator_id" value="([^"]+)"', text)
                csrf_match = re.search(r'name="_token" value="([^"]+)"', text)
                
                if not creator_id_match or not csrf_match:
                    return None
                
                return {
                    "creator_id": creator_id_match.group(1),
                    "csrf_token": csrf_match.group(1),
                    "cookies": resp.cookies
                }

    async def create_payment(self, username, amount, payer_name, payer_email, message):
        data = await self.get_creator_data(username)
        if not data:
            raise ValueError("Creator not found")

        payload = {
            "creator_id": data["creator_id"],
            "quantity": 1,
            "unit": amount, 
            "payment_method": "qris",
            "supporter_name": payer_name,
            "supporter_email": payer_email,
            "message": message,
            "is_private": 0,
            "_token": data["csrf_token"]
        }

        async with aiohttp.ClientSession(cookies=data["cookies"]) as session:
            async with session.post(f"{self.base_url}/tip/store", data=payload, headers=self.headers) as resp:
                result = await resp.json()
                
                if not result.get("success"):
                    raise ValueError("Failed to create transaction")
                
                order_id = result.get("order_id")
                return await self.get_qris_data(session, order_id)

    async def get_qris_data(self, session, order_id):
        async with session.get(f"{self.base_url}/payment/status/{order_id}") as resp:
            text = await resp.text()
            
            qr_match = re.search(r'img src="(https://trakteer.id/storage/images/qris/[^"]+)"', text)
            if qr_match:
                return {
                    "transaction_id": order_id,
                    "qr_image_url": qr_match.group(1),
                    "amount": 0 
                }
            return None

    async def check_paid_status(self, order_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/payment/check-status/{order_id}", headers=self.headers) as resp:
                data = await resp.json()
                return data.get("status") == "paid"
