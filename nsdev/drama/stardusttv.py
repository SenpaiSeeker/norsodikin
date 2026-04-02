from typing import Any, Dict

import httpx


class StardustTVAPI:
    def __init__(self, token: str, lang: str = "id"):
        self.base_url = "https://stardusttv.dramabos.my.id"
        self.token = token
        self.lang = lang

    async def langs(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/v1/langs")
            return response.json()

    async def list_drama(self, page: int = 1) -> Dict[str, Any]:
        params = {"page": str(page), "lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/v1/list", params=params)
            return response.json()

    async def find(self, query: str) -> Dict[str, Any]:
        params = {"q": query, "lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/v1/find", params=params)
            return response.json()

    async def detail(self, slug: str, drama_id: str) -> Dict[str, Any]:
        params = {"slug": slug, "id": drama_id, "lang": self.lang, "code": self.token}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/v1/detail/{slug}/{drama_id}", params=params)
            return response.json()

    async def episode(self, slug: str, drama_id: str, episode: int = 1) -> Dict[str, Any]:
        params = {"slug": slug, "id": drama_id, "ep": str(episode), "lang": self.lang, "code": self.token}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/v1/detail/{slug}/{drama_id}/episode/{episode}", params=params)
            return response.json()
