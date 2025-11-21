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
        data_json = {
            "options": {
                "isPrefetch": False,
                "query": query,
                "scope": "pins",
                "no_fetch_context_on_resource": False
            },
            "context": {}
        }
        
        params = {
            "source_url": f"/search/pins/?q={query}&rs=typed",
            "data": json.dumps(data_json),
            "_": str(int(asyncio.get_event_loop().time() * 1000))
        }

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            try:
                response = await client.get(self.base_url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('resource_response', {}).get('data', {}).get('results', [])
                    
                    urls = []
                    for item in results:
                        images = item.get('images', {})
                        url = images.get('orig', {}).get('url')
                        if not url:
                            for size in ['1200x', '736x', '474x', '236x']:
                                if size in images and 'url' in images[size]:
                                    url = images[size]['url']
                                    break
                        
                        if url and url not in urls:
                            urls.append(url)
                        if len(urls) >= limit:
                            return urls
                    
                    if urls:
                        return urls

                search_url = f"https://www.pinterest.com/search/pins/?q={query}&rs=typed"
                web_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }
                
                page_response = await client.get(search_url, headers=web_headers)
                page_response.raise_for_status()
                html_content = page_response.text
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                unique_urls = set()
                
                img_tags = soup.find_all('img', {'src': re.compile(r'https://i\.pinimg\.com/')})
                for img in img_tags:
                    src = img.get('src')
                    if src:
                        hd_url = re.sub(r'/\d+x/', '/originals/', src)
                        unique_urls.add(hd_url)
                        if len(unique_urls) >= limit:
                            break
                
                if not unique_urls:
                    script_tags = soup.find_all('script', string=re.compile(r'https://i\.pinimg\.com/'))
                    for script in script_tags:
                        urls_in_script = re.findall(r'https://i\.pinimg\.com/[0-9x]+/[^\s"]+\.jpg', script.string)
                        for u in urls_in_script:
                            hd_url = re.sub(r'/\d+x/', '/originals/', u)
                            unique_urls.add(hd_url)
                            if len(unique_urls) >= limit:
                                break
                
                if unique_urls:
                    return list(unique_urls)
                
                raise ValueError("Tidak ditemukan gambar (Metode API & Scraping Gagal). Coba query lain atau periksa koneksi internet.")

            except httpx.RequestError as e:
                raise Exception(f"Pinterest Network Error: {e}")
            except json.JSONDecodeError as e:
                raise Exception(f"Pinterest JSON Parse Error: {e}")
            except Exception as e:
                raise Exception(f"Pinterest Error: {e}")

    async def get_image_bytes(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=20) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
            except httpx.RequestError as e:
                raise Exception(f"Error downloading image: {e}")
