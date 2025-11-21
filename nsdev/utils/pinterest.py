import asyncio
import httpx
import json
import re
from typing import List
from bs4 import BeautifulSoup

class Pinterest:
    def __init__(self):
        self.base_search_url = "https://www.pinterest.com/search/pins/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }

    async def search(self, query: str, limit: int = 9) -> List[str]:
        unique_urls = set()
        formatted_query = query.replace(" ", "%20")
        
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            for page in range(1, 4):
                if len(unique_urls) >= limit:
                    break

                url = f"{self.base_search_url}?q={formatted_query}&rs=typed"
                
                try:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                    html_text = response.text

                    soup = BeautifulSoup(html_text, "html.parser")
                    data_script = soup.find("script", {"id": "__PWS_DATA__"})
                    
                    if data_script:
                        try:
                            json_data = json.loads(data_script.string)
                            self._extract_from_pws_data(json_data, unique_urls)
                        except Exception:
                            pass

                    regex_pattern = r'https://i\.pinimg\.com/(?:[0-9]+x|originals)/[^"\'\s>]+\.(?:jpg|jpeg|png|webp)'
                    raw_urls = re.findall(regex_pattern, html_text)
                    
                    for url in raw_urls:
                        if len(unique_urls) >= limit:
                            break
                        hd_url = re.sub(r'/\d+x/', '/originals/', url)
                        if "s-media-cache" not in hd_url:
                            unique_urls.add(hd_url)

                except httpx.RequestError:
                    continue
                except Exception:
                    continue

                await asyncio.sleep(0.5)

        final_list = list(unique_urls)[:limit]
        
        if not final_list:
            raise ValueError(f"Tidak ditemukan gambar untuk query: '{query}'.")
            
        return final_list

    def _extract_from_pws_data(self, data, url_set):
        if isinstance(data, dict):
            if 'images' in data:
                images = data['images']
                target = images.get('originals') or images.get('orig') or images.get('736x')
                if target and 'url' in target:
                    url_set.add(target['url'])
            
            for k, v in data.items():
                self._extract_from_pws_data(v, url_set)
                
        elif isinstance(data, list):
            for item in data:
                self._extract_from_pws_data(item, url_set)

    async def get_image_bytes(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
            except httpx.RequestError as e:
                raise Exception(f"Error downloading image: {e}")
