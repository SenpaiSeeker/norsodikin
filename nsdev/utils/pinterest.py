import asyncio
import httpx
import json
import re
from typing import List, Any, Dict

class Pinterest:
    def __init__(self):
        self.base_url = "https://www.pinterest.com/search/pins/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Referer": "https://www.pinterest.com/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Upgrade-Insecure-Requests": "1",
        }

    def _find_image_urls_in_json(self, data: Any, found_urls: List[str], limit: int):
        if len(found_urls) >= limit:
            return

        if isinstance(data, dict):
            if "images" in data and isinstance(data["images"], dict):
                images = data["images"]
                url = (
                    images.get("orig", {}).get("url") or 
                    images.get("1200x", {}).get("url") or
                    images.get("600x315", {}).get("url") or
                    images.get("474x", {}).get("url") or 
                    images.get("236x", {}).get("url")
                )
                if url:
                    hd_url = url.replace("/236x/", "/originals/").replace("/474x/", "/originals/").replace("/564x/", "/originals/").replace("/736x/", "/originals/")
                    if hd_url not in found_urls:
                        found_urls.append(hd_url)
            
            for key, value in data.items():
                self._find_image_urls_in_json(value, found_urls, limit)
        
        elif isinstance(data, list):
            for item in data:
                self._find_image_urls_in_json(item, found_urls, limit)

    async def search(self, query: str, limit: int = 9) -> List[str]:
        encoded_query = query.replace(" ", "%20")
        url = f"{self.base_url}?q={encoded_query}&rs=typed"

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            try:
                response = await client.get(url, headers=self.headers)
                
                html_content = response.text
                image_urls = []

                match = re.search(r'<script id="__PWS_DATA__" type="application/json">(.+?)</script>', html_content)
                if match:
                    try:
                        json_data = json.loads(match.group(1))
                        self._find_image_urls_in_json(json_data, image_urls, limit)
                    except Exception:
                        pass
                
                if len(image_urls) < limit:
                    pattern_general = r'https://i\.pinimg\.com/[0-9x]+/[^"]+?\.jpg'
                    fallback_urls = re.findall(pattern_general, html_content)
                    
                    for u in fallback_urls:
                        if len(image_urls) >= limit:
                            break
                        
                        hd_url = u.replace("/236x/", "/originals/").replace("/474x/", "/originals/").replace("/564x/", "/originals/").replace("/736x/", "/originals/")
                        
                        if hd_url not in image_urls:
                            image_urls.append(hd_url)

                if not image_urls:
                     raise ValueError("Tidak ditemukan gambar.")

                return image_urls[:limit]

            except Exception as e:
                raise Exception(f"Gagal mengambil data Pinterest: {e}")

    async def get_image_bytes(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
