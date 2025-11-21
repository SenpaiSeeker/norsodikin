import asyncio
import httpx
import json
import re
import urllib.parse
from typing import List
from bs4 import BeautifulSoup

class Pinterest:
    def __init__(self):
        self.base_search_url = "https://www.pinterest.com/search/pins/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Referer": "https://www.google.com/",
        }

    async def search(self, query: str, limit: int = 9) -> List[str]:
        unique_urls = set()
        formatted_query = urllib.parse.quote(query)
        
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            url = f"{self.base_search_url}?q={formatted_query}"
            
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                html_text = response.text

                soup = BeautifulSoup(html_text, "html.parser")
                data_script = soup.find("script", {"id": "__PWS_DATA__"})
                
                if data_script:
                    try:
                        json_data = json.loads(data_script.string)
                        self._extract_from_json(json_data, unique_urls)
                    except Exception:
                        pass

                regex_pattern = r'https://i\.pinimg\.com/(?:[0-9]+x|originals)/[^"\'\s>]+\.(?:jpg|jpeg|webp)'
                raw_urls = re.findall(regex_pattern, html_text)
                
                for url in raw_urls:
                    if len(unique_urls) >= limit:
                        break
                    hd_url = re.sub(r'/\d+x/', '/originals/', url)
                    if "s-media-cache" not in hd_url and "75x75" not in url: 
                        unique_urls.add(hd_url)

            except Exception as e:
                raise Exception(f"Pinterest Network Error: {e}")

        final_list = list(unique_urls)[:limit]
        
        if not final_list:
            raise ValueError(f"Pinterest memblokir bot atau query '{query}' tidak ditemukan. (Terdeteksi Login Wall)")
            
        return final_list

    def _extract_from_json(self, data, url_set):
        if isinstance(data, dict):
            if 'images' in data and isinstance(data['images'], dict):
                images = data['images']
                target = images.get('orig') or images.get('originals') or images.get('474x')
                if target and 'url' in target:
                    url = target['url']
                    if not url.endswith('.png'): 
                        url_set.add(url)
            
            for k, v in data.items():
                self._extract_from_json(v, url_set)
                
        elif isinstance(data, list):
            for item in data:
                self._extract_from_json(item, url_set)

    async def get_image_bytes(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.content
            except httpx.RequestError as e:
                raise Exception(f"Error downloading image: {e}")
