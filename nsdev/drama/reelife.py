from typing import Any, Dict

import httpx


class ReelifeAPI:
    def __init__(self, token: str, lang: str = "in"):
        self.base_url = "https://reelife.dramabos.my.id"
        self.token = token
        self.lang = lang

    async def home(self, page: int = 1) -> Dict[str, Any]:
        params = {"page": str(page), "lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/home", params=params)
            return response.json()

    async def browse(self, page: int = 1, letter: str = "a") -> Dict[str, Any]:
        params = {"page": str(page), "letter": letter, "lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/browse", params=params)
            return response.json()

    async def search(self, query: str, page: int = 1) -> Dict[str, Any]:
        params = {"q": query, "page": str(page), "lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/search", params=params)
            return response.json()

    async def suggest(self, query: str) -> Dict[str, Any]:
        params = {"q": query, "lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/suggest", params=params)
            return response.json()

    async def rank(self, rank_type: str = "trending") -> Dict[str, Any]:
        params = {"type": rank_type, "lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/rank", params=params)
            return response.json()

    async def book_detail(self, book_id: str) -> Dict[str, Any]:
        params = {"id": book_id, "lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/book/{book_id}", params=params)
            return response.json()

    async def chapters(self, book_id: str) -> Dict[str, Any]:
        params = {"id": book_id, "lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/book/{book_id}/chapters", params=params)
            return response.json()

    async def episode_detail(self, book_id: str, chapter_id: str, preload: int = 3) -> Dict[str, Any]:
        params = {
            "bookId": book_id,
            "chapterId": chapter_id,
            "preload": str(preload),
            "code": self.token,
            "lang": self.lang,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/book/{book_id}/episode/{chapter_id}", params=params)
            return response.json()

    async def play(self, book_id: str, chapter_id: str) -> Dict[str, Any]:
        params = {"bookId": book_id, "chapterId": chapter_id, "code": self.token, "lang": self.lang}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/play/{book_id}/{chapter_id}", params=params)
            return response.json()
