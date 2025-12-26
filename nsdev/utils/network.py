import asyncio
import cloudscraper
from functools import partial

class AsyncScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()

    async def get(self, url, headers=None, params=None):
        loop = asyncio.get_running_loop()
        func = partial(self.scraper.get, url, headers=headers, params=params)
        response = await loop.run_in_executor(None, func)
        return response

    async def post(self, url, headers=None, data=None, json=None):
        loop = asyncio.get_running_loop()
        func = partial(self.scraper.post, url, headers=headers, data=data, json=json)
        response = await loop.run_in_executor(None, func)
        return response

    async def get_text(self, url):
        response = await self.get(url)
        return response.text

    async def get_json(self, url):
        response = await self.get(url)
        return response.json()
