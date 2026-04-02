from typing import Any, Dict, Optional

import httpx


class NetShortAPI:
    def __init__(self, token: str, lang: str = "in"):
        self.base_url = "https://netshort.dramabos.my.id"
        self.token = token
        self.lang = lang

    async def home(self, page: int = 1) -> Dict[str, Any]:
        params = {"lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/home/{page}", params=params)
            return response.json()

    async def categories(self) -> Dict[str, Any]:
        params = {"lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/categories", params=params)
            return response.json()

    async def list_drama(
        self,
        page: int = 1,
        region: Optional[str] = None,
        audio: Optional[str] = None,
        tag: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {"lang": self.lang}
        if region:
            params["region"] = region
        if audio:
            params["audio"] = audio
        if tag:
            params["tag"] = tag
        if sort:
            params["sort"] = sort
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/list/{page}", params=params)
            return response.json()

    async def detail(self, drama_id: str) -> Dict[str, Any]:
        params = {"id": drama_id, "lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/drama/{drama_id}", params=params)
            return response.json()

    async def watch(self, drama_id: str, episode: int = 1) -> Dict[str, Any]:
        params = {"id": drama_id, "ep": str(episode), "lang": self.lang, "code": self.token}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/watch/{drama_id}/{episode}", params=params)
            return response.json()

    async def search(self, query: str, page: int = 1) -> Dict[str, Any]:
        params = {"lang": self.lang, "q": query, "page": str(page)}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/search", params=params)
            return response.json()
