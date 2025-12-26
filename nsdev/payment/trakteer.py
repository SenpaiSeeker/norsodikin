import re
import json
from ..utils.network import AsyncScraper

class TrakteerScraper:
    def __init__(self):
        self.http = AsyncScraper()
        self.base_url = "https://trakteer.id"

    async def get_page_info(self, page_url):
        if "trakteer.id/" not in page_url:
            return None
        
        username = page_url.split("trakteer.id/")[-1].split("/")[0]
        html = await self.http.get_text(page_url)
        
        csrf_match = re.search(r'name="csrf-token" content="([^"]+)"', html)
        creator_name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        
        if not csrf_match:
            return None

        return {
            "username": username,
            "csrf_token": csrf_match.group(1),
            "creator_name": creator_name_match.group(1) if creator_name_match else username
        }

    async def create_payment(self, page_url, sender_name, sender_email, quantity=1, message="Support"):
        info = await self.get_page_info(page_url)
        if not info:
            raise Exception("Gagal mengambil info halaman Trakteer")

        headers = {
            "X-CSRF-TOKEN": info["csrf_token"],
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": page_url,
            "X-Requested-With": "XMLHttpRequest"
        }

        payload = {
            "payment-method": "qris",
            "display-name": sender_name,
            "email": sender_email,
            "content": message,
            "unit": quantity,
            "is_private": "0"
        }

        post_url = f"{self.base_url}/payment/init"
        response = await self.http.post(post_url, headers=headers, data=payload)
        
        try:
            data = response.json()
            if not data.get("success"):
                raise Exception("Gagal inisialisasi pembayaran")
            
            order_id = data.get("order_id")
            return await self.get_qris_image(order_id)
            
        except json.JSONDecodeError:
            raise Exception("Respon Trakteer tidak valid")

    async def get_qris_image(self, order_id):
        url = f"{self.base_url}/payment/status/{order_id}"
        html = await self.http.get_text(url)
        
        qris_match = re.search(r'src="([^"]+qris[^"]+)"', html)
        amount_match = re.search(r'Rp\s+([\d\.]+)', html)
        
        if qris_match:
            return {
                "transaction_id": order_id,
                "qris_url": qris_match.group(1),
                "amount": amount_match.group(1).replace(".", "") if amount_match else "0"
            }
        raise Exception("QRIS tidak ditemukan")

    async def check_status(self, order_id):
        url = f"{self.base_url}/payment/check-status/{order_id}"
        data = await self.http.get_json(url)
        return data.get("status") == "success"
