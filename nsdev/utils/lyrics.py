import httpx
from types import SimpleNamespace

class LyricsFinder:
    def __init__(self):
        self.api_url = "https://lrclib.net/api/search"

    async def search(self, query: str):
        params = {"q": query}
        async with httpx.AsyncClient() as client:
            response = await client.get(self.api_url, params=params)
            data = response.json()
            if not data:
                return None
            
            track = data[0]
            return SimpleNamespace(
                title=track.get("name"),
                artist=track.get("artistName"),
                album=track.get("albumName"),
                lyrics=track.get("plainLyrics"),
                synced=track.get("syncedLyrics")
            )
