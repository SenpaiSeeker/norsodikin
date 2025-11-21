import asyncio
import httpx
import json
import re
from typing import List
from bs4 import BeautifulSoup

class Pinterest:
    def __init__(self):
        self.base_url = "https://www.pinterest.com/resource/BaseSearchResource/get/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.pinterest.com/",
            "X-Pinterest-AppState": "active",
            "X-Requested-With": "XMLHttpRequest",
        }

    async def search(self, query: str, limit: int = 9) -> List[str]:
        unique_urls = set()
        
        search_url = f"https://www.pinterest.com/search/pins/?q={query}&rs=typed"
        web_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            try:
                page_response = await client.get(search_url, headers=web_headers)
                page_response.raise_for_status()
                html_content = page_response.text
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                img_tags = soup.find_all('img', src=re.compile(r'https://i\.pinimg\.com/'))
                for img in img_tags:
                    src = img.get('src')
                    if src:
                        hd_url = re.sub(r'/\d+x/', '/originals/', src)
                        unique_urls.add(hd_url)
                        if len(unique_urls) >= limit:
                            break
                
                if len(unique_urls) < limit:
                    script_tags = soup.find_all('script')
                    for script in script_tags:
                        if script.string:
                            urls_in_script = re.findall(r'https://i\.pinimg\.com/[0-9x]+/[^\s"]+\.(jpg|jpeg|png)', script.string, re.IGNORECASE)
                            for match in urls_in_script:
                                url = match[0] if isinstance(match, tuple) else match
                                hd_url = re.sub(r'/\d+x/', '/originals/', url)
                                unique_urls.add(hd_url)
                                if len(unique_urls) >= limit:
                                    break
                
                if len(unique_urls) < limit:
                    json_scripts = soup.find_all('script', {'type': 'application/json'})
                    for script in json_scripts:
                        try:
                            json_data = json.loads(script.string)
                            self._extract_urls_from_json(json_data, unique_urls, limit)
                        except json.JSONDecodeError:
                            continue
                
                if len(unique_urls) < limit:
                    for page in range(2, 5):
                        next_url = f"{search_url}&page={page}"
                        next_response = await client.get(next_url, headers=web_headers)
                        if next_response.status_code == 200:
                            next_soup = BeautifulSoup(next_response.text, 'html.parser')
                            next_imgs = next_soup.find_all('img', src=re.compile(r'https://i\.pinimg\.com/'))
                            for img in next_imgs:
                                src = img.get('src')
                                if src:
                                    hd_url = re.sub(r'/\d+x/', '/originals/', src)
                                    unique_urls.add(hd_url)
                                    if len(unique_urls) >= limit:
                                        break
                        if len(unique_urls) >= limit:
                            break
                
                if unique_urls:
                    return list(unique_urls)
                
                raise ValueError("Tidak ditemukan gambar (Scraping Gagal). Coba query lain atau periksa koneksi internet. Pinterest mungkin memerlukan autentikasi atau struktur telah berubah.")

            except httpx.RequestError as e:
                raise Exception(f"Pinterest Network Error: {e}")
            except Exception as e:
                raise Exception(f"Pinterest Error: {e}")

    def _extract_urls_from_json(self, data, unique_urls, limit):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == 'images' and isinstance(value, dict):
                    for size, img_data in value.items():
                        if isinstance(img_data, dict) and 'url' in img_data:
                            url = img_data['url']
                            hd_url = re.sub(r'/\d+x/', '/originals/', url)
                            unique_urls.add(hd_url)
                            if len(unique_urls) >= limit:
                                return
                else:
                    self._extract_urls_from_json(value, unique_urls, limit)
        elif isinstance(data, list):
            for item in data:
                self._extract_urls_from_json(item, unique_urls, limit)

    async def get_image_bytes(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
            except httpx.RequestError as e:
                raise Exception(f"Error downloading image: {e}")
