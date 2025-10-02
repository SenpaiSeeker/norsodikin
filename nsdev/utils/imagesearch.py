import asyncio
import random
from typing import List

import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


class ImageSearch:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.headers = {"User-Agent": UserAgent().random}

    async def _fetch_image_urls(self, query: str, type: str) -> List[str]:
        search_url = f"https://duckduckgo.com/?q={query}&t=h_&iax=images&ia=images"
        if type == "gif":
            search_url = f"https://duckduckgo.com/?q={query}&t=h_&iax=images&ia=images&atb=v314-1&strict_dd=w&pn=1"

        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
            response = await client.get(search_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            
            image_urls = []
            script_tags = soup.find_all("script")
            for script in script_tags:
                if "vqd" in str(script):
                    matches = re.findall(r'"(https?://[^"]+\.(?:png|jpg|jpeg|gif|webp))"', str(script))
                    for url in matches:
                        if type == "gif" and url.lower().endswith("gif"):
                            image_urls.append(url)
                        elif type == "image" and not url.lower().endswith("gif"):
                            image_urls.append(url)
            
            return list(set(image_urls))


    async def search_image(self, query: str, limit: int = 5) -> List[str]:
        urls = await self._fetch_image_urls(query, "image")
        random.shuffle(urls)
        return urls[:limit]

    async def search_gif(self, query: str, limit: int = 5) -> List[str]:
        urls = await self._fetch_image_urls(query, "gif")
        random.shuffle(urls)
        return urls[:limit]

    async def random_image(self, limit: int = 1) -> List[str]:
        random_queries = ["nature", "abstract", "cityscape", "animals", "flowers", "mountain"]
        query = random.choice(random_queries)
        return await self.search_image(query, limit)

    async def random_gif(self, limit: int = 1) -> List[str]:
        random_queries = ["funny", "cute", "reaction", "meme", "animation"]
        query = random.choice(random_queries)
        return await self.search_gif(query, limit)
