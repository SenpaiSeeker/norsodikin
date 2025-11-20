import asyncio
import httpx
import re
from typing import List

class Pinterest:
    def __init__(self):
        self.base_url = "https://duckduckgo.com/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

    async def search(self, query: str, limit: int = 9) -> List[str]:
        full_query = f"{query} site:pinterest.com"
        
        async with httpx.AsyncClient(timeout=20) as client:
            try:
                res = await client.get(self.base_url, params={"q": full_query}, headers=self.headers)
                vqd_match = re.search(r'vqd=([\d-]+)', res.text)
                if not vqd_match:
                    vqd_match = re.search(r'vqd\s?=\s?[\'"]([\d-]+)[\'"]', res.text)
                
                if not vqd_match:
                    raise Exception("Gagal mendapatkan token pencarian.")
                
                vqd = vqd_match.group(1)

                params = {
                    "l": "us-en",
                    "o": "json",
                    "q": full_query,
                    "vqd": vqd,
                    "f": ",,,",
                    "p": "1",
                    "v7exp": "a"
                }
                
                api_url = "https://duckduckgo.com/i.js"
                res_images = await client.get(api_url, params=params, headers=self.headers)
                data = res_images.json()
                
                results = data.get("results", [])
                
                images = []
                for item in results:
                    img_url = item.get("image")
                    if img_url:
                        images.append(img_url)
                    
                    if len(images) >= limit:
                        break
                
                return images

            except Exception as e:
                raise Exception(f"Gagal mencari gambar: {e}")

    async def get_image_bytes(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
