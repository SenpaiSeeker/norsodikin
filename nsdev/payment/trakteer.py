import aiohttp
import re
import json
import uuid

class TrakteerScraper:
    def __init__(self):
        self.base_url = "https://trakteer.id"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
            "Referer": "https://trakteer.id/",
            "Origin": "https://trakteer.id",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Upgrade-Insecure-Requests": "1"
        }

    async def get_creator_data(self, username):
        url = f"{self.base_url}/{username}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                if resp.status != 200:
                    return None
                
                text = await resp.text()
                
                creator_id_match = re.search(r'name=["\']creator_id["\'][^>]*value=["\']([^"\']+)["\']', text)
                if not creator_id_match:
                    creator_id_match = re.search(r'value=["\']([^"\']+)["\'][^>]*name=["\']creator_id["\']', text)

                csrf_match = re.search(r'name=["\']csrf-token["\'][^>]*content=["\']([^"\']+)["\']', text)
                
                if not creator_id_match or not csrf_match:
                    return None
                
                return {
                    "creator_id": creator_id_match.group(1),
                    "csrf_token": csrf_match.group(1),
                    "cookies": session.cookie_jar.filter_cookies(self.base_url)
                }

    async def create_payment(self, username, amount, payer_name, payer_email, message):
        data = await self.get_creator_data(username)
        if not data:
            raise ValueError(f"Creator '{username}' not found or page structure changed.")

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

        post_headers = self.headers.copy()
        post_headers.update({
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": f"{self.base_url}/{username}",
            "X-CSRF-TOKEN": data["csrf_token"]
        })

        async with aiohttp.ClientSession(cookies=data["cookies"]) as session:
            async with session.post(f"{self.base_url}/tip/store", data=payload, headers=post_headers) as resp:
                try:
                    result = await resp.json()
                except Exception:
                    text_err = await resp.text()
                    raise ValueError(f"Server returned non-JSON response: {text_err[:100]}")
                
                if not result.get("success"):
                    raise ValueError(f"Failed to create transaction: {result}")
                
                order_id = result.get("order_id")
                
                return await self.get_qris_data(session, order_id)

    async def get_qris_data(self, session, order_id):
        url = f"{self.base_url}/payment/status/{order_id}"
        async with session.get(url, headers=self.headers) as resp:
            text = await resp.text()
            
            qr_match = re.search(r'src=["\'](https://trakteer\.id/storage/images/qris/[^"\']+)["\']', text)
            
            if not qr_match:
                qr_match = re.search(r'src=["\']([^"\']*/qris/[^"\']+)["\']', text)

            if qr_match:
                return {
                    "transaction_id": order_id,
                    "qr_image_url": qr_match.group(1),
                    "amount": 0,
                    "status_url": url
                }
            
            raise ValueError("QRIS Image not found in payment page")

    async def check_paid_status(self, order_id):
        check_headers = self.headers.copy()
        check_headers["X-Requested-With"] = "XMLHttpRequest"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/payment/check-status/{order_id}", headers=check_headers) as resp:
                try:
                    data = await resp.json()
                    return data.get("status") == "paid" or data.get("status") == True
                except:
                    return False
