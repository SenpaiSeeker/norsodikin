import httpx
from typing import Optional, Dict, Any

class DramaBiteAPI:
    def __init__(self, token: str, lang: str = "id"):
        self.base_url = "https://dramabite.dramabos.my.id"
        self.token = token
        self.lang = lang
        self.session = httpx.AsyncClient()

    async def languages(self) -> Dict[str, Any]:
        response = await self.session.get(f"{self.base_url}/languages")
        return response.json()

    async def home(self) -> Dict[str, Any]:
        params = {"lang": self.lang}
        response = await self.session.get(f"{self.base_url}/home", params=params)
        return response.json()

    async def module(self, page: int = 1) -> Dict[str, Any]:
        params = {"page": str(page), "lang": self.lang}
        response = await self.session.get(f"{self.base_url}/module", params=params)
        return response.json()

    async def search(self, query: str) -> Dict[str, Any]:
        params = {"q": query, "lang": self.lang}
        response = await self.session.get(f"{self.base_url}/search", params=params)
        return response.json()

    async def detail(self, cid: str) -> Dict[str, Any]:
        params = {"cid": cid, "lang": self.lang}
        response = await self.session.get(f"{self.base_url}/drama/{cid}", params=params)
        return response.json()

    async def episodes(self, cid: str) -> Dict[str, Any]:
        params = {"cid": cid, "lang": self.lang, "code": self.token}
        response = await self.session.get(f"{self.base_url}/episodes/{cid}", params=params)
        return response.json()

    async def play(self, cid: str, vid: str) -> Dict[str, Any]:
        params = {"cid": cid, "vid": vid, "lang": self.lang, "code": self.token}
        response = await self.session.get(f"{self.base_url}/play/{cid}/{vid}", params=params)
        return response.json()

    async def close(self):
        await self.session.aclose()
