import httpx
import asyncio

class PasteClient:
    def __init__(self, token: str):
        self.token = token
        self.post_url = "https://api.github.com/gists"

    async def paste(self, text: str, filename="paste.md") -> str:
        payload = {
            "public": True,
            "files": {
                filename: {
                    "content": text
                }
            }
        }

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json"
        }

        async with httpx.AsyncClient(headers=headers) as client:
            r = await client.post(self.post_url, json=payload)
            r.raise_for_status()
            return r.json()["html_url"]


