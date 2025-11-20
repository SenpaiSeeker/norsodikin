import asyncio
import httpx
import re
from typing import List

class Pinterest:
    def __init__(self):
        self.base_url = "https://www.pinterest.com/search/pins/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.pinterest.com/",
        }

    async def search(self, query: str, limit: int = 9) -> List[str]:
        encoded_query = query.replace(" ", "%20")
        url = f"{self.base_url}?q={encoded_query}&rs=typed"

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                html_content = response.text

                pattern = r'https://i\.pinimg\.com/\d+x/[a-f0-9]+/[a-f0-9]+/[a-f0-9]+/[a-f0-9]+\.jpg'
                
                found_urls = re.findall(pattern, html_content)
                
                unique_urls = []
                seen = set()
                
                for img_url in found_urls:
                    high_res_url = re.sub(r'/\d+x/', '/originals/', img_url)
                    
                    if high_res_url not in seen:
                        unique_urls.append(high_res_url)
                        seen.add(high_res_url)
                    
                    if len(unique_urls) >= limit:
                        break
                
                if not unique_urls:
                    pattern_std = r'https://i\.pinimg\.com/564x/[a-f0-9]+/[a-f0-9]+/[a-f0-9]+/[a-f0-9]+\.jpg'
                    found_std = re.findall(pattern_std, html_content)
                    for img_url in found_std:
                         if img_url not in seen:
                            unique_urls.append(img_url)
                            seen.add(img_url)
                         if len(unique_urls) >= limit:
                            break
                
                return unique_urls

            except Exception as e:
                raise Exception(f"Gagal mengambil data dari Pinterest: {e}")

    async def get_image_bytes(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
