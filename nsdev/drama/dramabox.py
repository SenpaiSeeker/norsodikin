from typing import Any, Dict

import httpx


class DramaboxAPI:
    def __init__(self, token: str, lang: str = "in"):
        self.base_url = "https://dramabox.dramabos.my.id"
        self.token = token
        self.lang = lang

    async def homepage(self, page: int = 1) -> Dict[str, Any]:
        params = {"page": str(page), "lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/homepage", params=params)
            return response.json()

    async def dubbed(self, classify: str = "terpopuler", page: int = 1) -> Dict[str, Any]:
        params = {"classify": classify, "page": str(page), "lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/dubbed", params=params)
            return response.json()

    async def foryou(self) -> Dict[str, Any]:
        params = {"lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/foryou", params=params)
            return response.json()

    async def latest(self) -> Dict[str, Any]:
        params = {"lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/latest", params=params)
            return response.json()

    async def populersearch(self) -> Dict[str, Any]:
        params = {"lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/populersearch", params=params)
            return response.json()

    async def search(self, query: str) -> Dict[str, Any]:
        params = {"query": query, "lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/search", params=params)
            return response.json()

    async def detail(self, bookId: str) -> Dict[str, Any]:
        params = {"bookId": bookId, "lang": self.lang, "code": self.token}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/detail", params=params)
            return response.json()

    async def allepisode(self, bookId: str) -> Dict[str, Any]:
        params = {"bookId": bookId, "code": self.token}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/allepisode", params=params)
            return response.json()
