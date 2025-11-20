import asyncio
import httpx
import json
import re
from typing import List

class Pinterest:
    def __init__(self):
        self.base_url = "https://www.pinterest.com/resource/BaseSearchResource/get/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.pinterest.com/",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }

    async def search(self, query: str, limit: int = 9) -> List[str]:
        import time
        timestamp = int(time.time() * 1000)
        
        options = {
            "isPrefetch": False,
            "query": query,
            "scope": "pins",
            "no_fetch_context_on_resource": False
        }
        
        data_json = json.dumps({"options": options, "context": {}})
        
        params = {
            "source_url": f"/search/pins/?q={query}&rs=typed",
            "data": data_json,
            "module_path": f"App()>SearchPage(resource=BaseSearchResource(options={json.dumps(options)}))",
            "_": timestamp
        }

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            try:
                await client.get("https://www.pinterest.com/")
                
                response = await client.get(self.base_url, headers=self.headers, params=params)
                
                if response.status_code == 403:
                     return await self._fallback_google_search(query, limit)
                
                response.raise_for_status()
                data = response.json()
                
                results = data.get("resource_response", {}).get("data", {}).get("results", [])
                
                images = []
                for item in results:
                    if len(images) >= limit:
                        break

                    images_obj = item.get("images", {})
                    url = (
                        images_obj.get("orig", {}).get("url") or 
                        images_obj.get("474x", {}).get("url") or 
                        images_obj.get("236x", {}).get("url")
                    )
                    
                    if url:
                        images.append(url)
                
                return images

            except Exception as e:
                 return await self._fallback_google_search(query, limit)

    async def _fallback_google_search(self, query: str, limit: int) -> List[str]:
        google_url = "https://www.google.com/search"
        params = {
            "q": f"{query} site:pinterest.com",
            "tbm": "isch",
            "content-type": "image/png",
        }
        headers = {
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.get(google_url, params=params, headers=headers)
            html = res.text
            
            pattern = r'https://i\.pinimg\.com/[^"]+\.jpg'
            found_urls = re.findall(pattern, html)
            
            unique_urls = []
            seen = set()
            for url in found_urls:
                clean_url = url.encode().decode('unicode-escape')

                if "236x" in clean_url:
                    high_res = clean_url.replace("236x", "564x")
                    if high_res not in seen:
                        unique_urls.append(high_res)
                        seen.add(high_res)
                else:
                    if clean_url not in seen:
                        unique_urls.append(clean_url)
                        seen.add(clean_url)
                
                if len(unique_urls) >= limit:
                    break
            
            return unique_urls

    async def get_image_bytes(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
