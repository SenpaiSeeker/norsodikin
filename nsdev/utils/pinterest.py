import asyncio
import httpx
import json
import re
from typing import List

class Pinterest:
    def __init__(self):
        self.base_url = "https://www.pinterest.com/search/pins/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
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

                match = re.search(r'<script id="__PWS_DATA__" type="application/json">(.+?)</script>', html_content)
                
                if not match:
                    match = re.search(r'"results":(\[.*?\]),"term"', html_content)
                    if not match:
                         raise ValueError("Gagal menemukan data JSON Pinterest.")
                    
                    try:
                         results_raw = json.loads(match.group(1))
                         return self._extract_urls_from_list(results_raw, limit)
                    except:
                         raise ValueError("Gagal parsing JSON fallback.")

                json_data = json.loads(match.group(1))
                
                try:
                    feed_key = list(json_data['props']['initialReduxState']['feeds'].keys())[0]
                    results = json_data['props']['initialReduxState']['feeds'][feed_key]['items']
                    
                    pins_map = json_data['props']['initialReduxState']['pins']
                except (KeyError, IndexError):
                    raise ValueError("Struktur JSON Pinterest tidak dikenali.")

                image_urls = []
                for item in results:
                    if isinstance(item, dict):
                         continue
                    
                    pin_id = str(item)
                    pin_data = pins_map.get(pin_id)
                    
                    if not pin_data: 
                        continue
                        
                    images = pin_data.get("images", {})
                    url = (
                        images.get("orig", {}).get("url") or 
                        images.get("1200x", {}).get("url") or
                        images.get("600x315", {}).get("url") or
                        images.get("474x", {}).get("url") or 
                        images.get("236x", {}).get("url")
                    )
                    
                    if url and url not in image_urls:
                        image_urls.append(url)
                    
                    if len(image_urls) >= limit:
                        break
                
                return image_urls

            except Exception as e:
                fallback_urls = re.findall(r'https://i\.pinimg\.com/\d+x/[^"]+\.jpg', html_content)
                unique_fallback = []
                seen = set()
                for u in fallback_urls:
                    hd_url = re.sub(r'/\d+x/', '/originals/', u)
                    if hd_url not in seen:
                        unique_fallback.append(hd_url)
                        seen.add(hd_url)
                    if len(unique_fallback) >= limit:
                        break
                
                if unique_fallback:
                    return unique_fallback
                
                raise Exception(f"Gagal total mengambil data Pinterest: {e}")

    def _extract_urls_from_list(self, items: list, limit: int) -> List[str]:
        urls = []
        for item in items:
            try:
                url = item.get("images", {}).get("orig", {}).get("url")
                if url:
                    urls.append(url)
            except:
                pass
            if len(urls) >= limit:
                break
        return urls

    async def get_image_bytes(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
