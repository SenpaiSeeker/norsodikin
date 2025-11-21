import asyncio
import httpx
import json
import re
import os
from http.cookiejar import MozillaCookieJar
from typing import List
from bs4 import BeautifulSoup

class Pinterest:
    def __init__(self, cookies_file_path: str = "cookies/Pinterest.txt"):
        self.base_search_url = "https://www.pinterest.com/search/pins/"
        self.cookies_file_path = cookies_file_path
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.pinterest.com/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        }

    def _load_cookies(self):
        if self.cookies_file_path and os.path.exists(self.cookies_file_path):
            try:
                jar = MozillaCookieJar(self.cookies_file_path)
                jar.load(ignore_discard=True, ignore_expires=True)
                return jar
            except Exception:
                pass
        return None

    async def search(self, query: str, limit: int = 9) -> List[str]:
        unique_urls = set()
        formatted_query = query.replace(" ", "%20")
        cookie_jar = self._load_cookies()
        
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, cookies=cookie_jar) as client:
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

                    if len(unique_urls) < limit:
                        regex_pattern = r'https://i\.pinimg\.com/(?:[0-9]+x|originals)/([a-z0-9]{32,})\.(?:jpg|jpeg|png|webp)'
                        raw_matches = re.findall(regex_pattern, html_text)
                        
                        for hash_id in raw_matches:
                            hd_url = f"https://i.pinimg.com/originals/{hash_id[:2]}/{hash_id[2:4]}/{hash_id[4:6]}/{hash_id}.jpg"
                            unique_urls.add(hd_url)

                except httpx.RequestError:
                    continue
                except Exception:
                    continue

                await asyncio.sleep(0.5)

        final_list = list(unique_urls)[:limit]
        
        if not final_list:
            if not cookie_jar:
                raise ValueError(f"Gagal mengambil gambar. Cookie Pinterest tidak ditemukan atau kadaluarsa. Query: '{query}'")
            raise ValueError(f"Tidak ditemukan gambar untuk query: '{query}'. Pastikan cookie valid.")
            
        return final_list

    def _extract_from_pws_data(self, data, url_set):
        if isinstance(data, dict):
            if 'images' in data and 'orig' in data['images']:
                img_data = data['images']['orig']
                if 'url' in img_data:
                    url = img_data['url']
                    if "i.pinimg.com" in url and "75x75" not in url:
                        url_set.add(url)
            
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
