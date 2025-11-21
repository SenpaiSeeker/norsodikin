import asyncio
import httpx
import json
import re
from typing import List
from urllib.parse import urlencode

class Pinterest:
    def __init__(self):
        self.base_url = "https://www.pinterest.com"
        self.resource_url = "https://www.pinterest.com/resource/BaseSearchResource/get/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.pinterest.com/",
            "X-Requested-With": "XMLHttpRequest",
            "X-APP-VERSION": "c642044",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

    async def search(self, query: str, limit: int = 9) -> List[str]:
        unique_urls = set()
        
        data_payload = {
            "options": {
                "article": None,
                "appliedProductFilters": "---",
                "query": query,
                "scope": "pins",
                "auto_correction_disabled": False,
                "top_pin_id": "",
                "filters": None
            },
            "context": {}
        }

        params = {
            "source_url": f"/search/pins/?q={query}&rs=typed",
            "data": json.dumps(data_payload),
            "_": "1635864321234"
        }

        async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
            try:
                initial_resp = await client.get(self.base_url, headers=self.headers)
                csrf_token = "123456" 
                for cookie in initial_resp.cookies:
                    if cookie.name == "csrftoken":
                        csrf_token = cookie.value
                
                headers = self.headers.copy()
                headers["X-CSRFToken"] = csrf_token
                
                response = await client.get(self.resource_url, params=params, headers=headers, cookies=initial_resp.cookies)
                
                try:
                    response_json = response.json()
                except json.JSONDecodeError:
                    raise ValueError(f"Gagal decode JSON. Status: {response.status_code}. Pinterest mungkin memblokir IP atau meminta captcha.")

                if "resource_response" in response_json:
                    data = response_json["resource_response"].get("data", {})
                    results = data.get("results", [])
                    
                    for item in results:
                        if len(unique_urls) >= limit:
                            break
                            
                        images = item.get("images")
                        if not images:
                            continue
                            
                        target_img = images.get("orig") or images.get("originals") or images.get("736x")
                        
                        if target_img and "url" in target_img:
                            url = target_img["url"]
                            if not url.endswith((".jpg", ".png", ".jpeg", ".webp")):
                                continue
                                
                            if "d53b014d86a6b6761bf649a0ed813c2b" in url or "s-media-cache" in url:
                                continue
                                
                            hd_url = re.sub(r'/\d+x/', '/originals/', url)
                            unique_urls.add(hd_url)

                if not unique_urls and response.status_code == 200:
                    regex_pattern = r'https://i\.pinimg\.com/(?:[0-9]+x|originals)/[^"\'\s]+\.(?:jpg|jpeg|png|webp)'
                    raw_matches = re.findall(regex_pattern, response.text)
                    for m in raw_matches:
                        if len(unique_urls) >= limit:
                            break
                        if "d53b01" in m:
                            continue
                        unique_urls.add(re.sub(r'/\d+x/', '/originals/', m))

            except httpx.RequestError as e:
                raise Exception(f"Network Error: {e}")
            except Exception as e:
                raise Exception(f"Pinterest Error: {e}")

        final_list = list(unique_urls)[:limit]
        
        if not final_list:
            raise ValueError("Tidak ditemukan gambar (Scraping Kosong). Pinterest mungkin merespons dengan halaman login/captcha.")
            
        return final_list

    async def get_image_bytes(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
            except httpx.RequestError as e:
                raise Exception(f"Error downloading image: {e}")
