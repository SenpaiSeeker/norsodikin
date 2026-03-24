import httpx
import asyncio
from typing import Optional, Dict, Any

class MeloloAPI:
    def __init__(self, token: str, lang: str = "id"):
        self.base_url = "https://melolo.dramabos.my.id"
        self.token = token
        self.lang = lang
        self.session = httpx.AsyncClient()

    async def home(self, offset: int = 0) -> Dict[str, Any]:
        params = {"lang": self.lang, "offset": str(offset)}
        response = await self.session.get(f"{self.base_url}/api/home", params=params)
        return response.json()

    async def detail(self, drama_id: str) -> Dict[str, Any]:
        params = {"id": drama_id, "lang": self.lang}
        response = await self.session.get(f"{self.base_url}/api/detail/{drama_id}", params=params)
        return response.json()

    async def search(self, query: str) -> Dict[str, Any]:
        params = {"lang": self.lang, "q": query}
        response = await self.session.get(f"{self.base_url}/api/search", params=params)
        return response.json()

    async def video(self, vid: str) -> Dict[str, Any]:
        params = {"vid": vid, "lang": self.lang, "code": self.token}
        response = await self.session.get(f"{self.base_url}/api/video/{vid}", params=params)
        return response.json()

    async def close(self):
        await self.session.aclose()
