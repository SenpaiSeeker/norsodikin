import asyncio
import re
from typing import List, Optional
from .pin_engine import PinterestAPI, PinterestMedia

class Pinterest:
    def __init__(self):
        self.api = PinterestAPI()

    async def _run_sync(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    async def search(self, query: str, limit: int = 10) -> List[str]:
        response = await self._run_sync(self.api.get_search, query, limit)
        if not response:
            return []
        
        resource_response = response.get("resource_response", {})
        data = resource_response.get("data", {})
        results = data.get("results", [])
        
        medias = PinterestMedia.from_responses(results)
        urls = [media.src for media in medias if media.src]
        
        unique_urls = list(dict.fromkeys(urls))
        return unique_urls[:limit]

    async def get_images(self, url: str, limit: int = 10) -> List[str]:
        pin_match = re.search(r"pin/(\d+)", url)
        if pin_match:
            pin_id = pin_match.group(1)
            response = await self._run_sync(self.api.get_related_images, pin_id, limit)
            
            resource_response = response.get("resource_response", {})
            data = resource_response.get("data", [])
            
            medias = PinterestMedia.from_responses(data)
            urls = [media.src for media in medias if media.src]
            
            unique_urls = list(dict.fromkeys(urls))
            return unique_urls[:limit]
        
        elif "search" in url:
            query_match = re.search(r"q=([^&]+)", url)
            if query_match:
                query = query_match.group(1)
                return await self.search(query, limit)
        
        return await self.search(url, limit)

    async def get_media_objects(self, query: str, limit: int = 10) -> List[PinterestMedia]:
        response = await self._run_sync(self.api.get_search, query, limit)
        if not response:
            return []
            
        resource_response = response.get("resource_response", {})
        data = resource_response.get("data", {})
        results = data.get("results", [])
        
        return PinterestMedia.from_responses(results)[:limit]
