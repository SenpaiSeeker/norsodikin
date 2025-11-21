import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup


class Pinterest:
    def __init__(self, base_url: str = "https://www.pinterest.com", timeout: int = 20):
        self.base_url = base_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": self.base_url,
            "X-Pinterest-AppState": "active",
            "X-Requested-With": "XMLHttpRequest",
        }
        self.timeout = timeout
        self.client = httpx.AsyncClient(headers=self.headers, timeout=self.timeout, follow_redirects=True)

    async def close(self):
        await self.client.aclose()

    async def search(self, query: str, limit: int = 9) -> List[str]:
        try:
            bookmarks = [""]
            unique_urls = set()
            
            encoded_query = query.replace(" ", "%20")

            search_url = f"{self.base_url}/resource/BaseSearchResource/get/"
            
            params = {
                "source_url": f"/search/pins/?q={encoded_query}&rs=typed",
                "data": json.dumps({
                    "options": {
                        "isPrefetch": False,
                        "query": query,
                        "scope": "pins",
                        "no_fetch_context_on_resource": False
                    },
                    "context": {}
                }),
                "_": int(asyncio.get_running_loop().time() * 1000)
            }
            
            for _ in range(3): 
                if len(unique_urls) >= limit:
                    break

                if bookmarks[-1]:
                    data_dict = json.loads(params["data"])
                    data_dict["options"]["bookmarks"] = [bookmarks[-1]]
                    params["data"] = json.dumps(data_dict)

                response = await self.client.get(search_url, params=params)
                response.raise_for_status()
                
                json_data = response.json()
                
                resource_response = json_data.get("resource_response", {})
                data = resource_response.get("data", {})
                results = data.get("results", []) if isinstance(data, dict) else data

                if not results:
                    break

                for item in results:
                    if len(unique_urls) >= limit:
                        break
                        
                    if "images" in item:
                        images = item["images"]
                        target = images.get("orig") or images.get("736x")
                        if target and target.get("url"):
                            unique_urls.add(target["url"])

                if "bookmark" in resource_response:
                    bookmarks.append(resource_response["bookmark"])
                else:
                    break

                await asyncio.sleep(0.5)

            if not unique_urls:
                return await self._search_fallback_html(query, limit)

            return list(unique_urls)[:limit]

        except Exception:
            return await self._search_fallback_html(query, limit)

    async def _search_fallback_html(self, query: str, limit: int) -> List[str]:
        unique_urls = set()
        encoded_query = query.replace(" ", "%20")
        url = f"{self.base_url}/search/pins/?q={encoded_query}&rs=typed"
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            html_content = response.text
            
            soup = BeautifulSoup(html_content, "html.parser")
            script_tag = soup.find("script", {"id": "__PWS_DATA__"}) or soup.find("script", {"id": "initial-state"})

            if script_tag:
                try:
                    data = json.loads(script_tag.string)
                    self._extract_urls_recursive(data, unique_urls, limit)
                except Exception:
                    pass
            
            if len(unique_urls) < limit:
                 regex_pattern = r'https://i\.pinimg\.com/(?:[0-9]+x|originals)/[^"\'\s>]+\.(?:jpg|jpeg|png|webp)'
                 raw_urls = re.findall(regex_pattern, html_content)
                 for raw_url in raw_urls:
                    if len(unique_urls) >= limit:
                        break
                    hd_url = re.sub(r'/\d+x/', '/originals/', raw_url)
                    unique_urls.add(hd_url)
            
            if not unique_urls:
                 raise ValueError(f"Tidak ditemukan gambar untuk: {query}")

            return list(unique_urls)[:limit]

        except Exception as e:
             raise Exception(f"Gagal mencari gambar Pinterest: {str(e)}")

    def _extract_urls_recursive(self, data, url_set, limit):
        if len(url_set) >= limit:
            return

        if isinstance(data, dict):
            if "images" in data:
                 images = data["images"]
                 target = images.get("orig") or images.get("originals") or images.get("736x")
                 if target and isinstance(target, dict) and "url" in target:
                     url_set.add(target["url"])
            
            for k, v in data.items():
                self._extract_urls_recursive(v, url_set, limit)
        
        elif isinstance(data, list):
            for item in data:
                self._extract_urls_recursive(item, url_set, limit)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
