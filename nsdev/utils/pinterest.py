import asyncio
import httpx
import re
from types import SimpleNamespace
from typing import List

class Pinterest:
    def __init__(self):
        self.base_url = "https://www.pinterest.com/resource/BaseSearchResource/get/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.pinterest.com/",
        }

    async def search(self, query: str, limit: int = 9) -> List[str]:
        params = {
            "source_url": f"/search/pins/?q={query}",
            "data": '{"options":{"isPrefetch":false,"query":"' + query + '","scope":"pins","no_fetch_context_on_resource":false},"context":{}}',
            "module_path": f"App()>SearchPage(resource=BaseSearchResource(options={{query:{query},scope:pins,no_fetch_context_on_resource:false}}))",
        }

        async with httpx.AsyncClient(timeout=20) as client:
            try:
                response = await client.get(self.base_url, headers=self.headers, params=params)
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
                raise Exception(f"Gagal mengambil data dari Pinterest: {e}")

    async def get_image_bytes(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
