import asyncio
import httpx
import json
import re
import os
from http.cookiejar import MozillaCookieJar
from typing import List, Optional, Dict
from bs4 import BeautifulSoup

class Pinterest:
    def __init__(self, cookie_path: str = "pinterest.txt"):
        self.base_search_url = "https://www.pinterest.com/search/pins/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }
        self.cookie_path = cookie_path
        self.cookies = self._load_cookies()

    def _load_cookies(self) -> Dict[str, str]:
        cookie_dict = {}
        if os.path.exists(self.cookie_path):
            try:
                cj = MozillaCookieJar(self.cookie_path)
                cj.load(ignore_discard=True, ignore_expires=True)
                for cookie in cj:
                    cookie_dict[cookie.name] = cookie.value
            except Exception:
                pass
        return cookie_dict

    async def search(self, query: str, limit: int = 9) -> List[str]:
        unique_urls = set()
        formatted_query = query.replace(" ", "%20")
        
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, cookies=self.cookies) as client:
            for page in range(1, 4):
                if len(unique_urls) >= limit:
                    break

                url = f"{self.base_search_url}?q={formatted_query}&rs=typed"
                
                try:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                    html_text = response.text

                    if "pinterest.com/login" in str(response.url):
                        pass

                    soup = BeautifulSoup(html_text, "html.parser")
                    data_script = soup.find("script", {"id": "__PWS_DATA__"})
                    
                    if data_script:
                        try:
                            json_data = json.loads(data_script.string)
                            self._extract_from_pws_data(json_data, unique_urls)
                        except Exception:
                            pass

                    regex_pattern = r'https://i\.pinimg\.com/(?:originals|736x)/[a-z0-9/]+\.(?:jpg|jpeg|png|webp)'
                    raw_urls = re.findall(regex_pattern, html_text)
                    
                    for url in raw_urls:
                        if len(unique_urls) >= limit:
                            break
                        
                        if "s-media-cache" in url or "75x75" in url or "236x" in url:
                            continue

                        hd_url = re.sub(r'/\d+x/', '/originals/', url)
                        unique_urls.add(hd_url)

                except httpx.RequestError:
                    continue
                except Exception:
                    continue

                await asyncio.sleep(0.5)

        final_list = list(unique_urls)[:limit]
        
        if not final_list:
            if not self.cookies:
                raise ValueError(f"Tidak ada gambar ditemukan. Login Pinterest diperlukan. Silakan simpan cookies Netscape di '{self.cookie_path}'")
            raise ValueError(f"Tidak ditemukan gambar valid untuk query: '{query}'. Struktur Pinterest mungkin berubah.")
            
        return final_list

    def _extract_from_pws_data(self, data, url_set):
        if isinstance(data, dict):
            if 'images' in data and isinstance(data['images'], dict):
                images = data['images']
                target = images.get('originals') or images.get('orig') or images.get('736x')
                if target and 'url' in target:
                    img_url = target['url']
                    if "i.pinimg.com" in img_url and not img_url.endswith(".gif"):
                        url_set.add(img_url)
            
            for k, v in data.items():
                if k != "user" and k != "owner": 
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
