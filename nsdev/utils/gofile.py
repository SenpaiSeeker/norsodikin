import random
from types import SimpleNamespace

import httpx


class GoFileUploader:
    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.api_base = "https://api.gofile.io"

    async def _get_server(self, client: httpx.AsyncClient) -> str:
        try:
            response = await client.get(f"{self.api_base}/servers")
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "ok":
                servers = data["data"]["servers"]
                return random.choice(servers)["name"]
            raise Exception("Could not retrieve a GoFile server list.")
        except (httpx.RequestError, KeyError, IndexError) as e:
            raise Exception(f"Failed to get GoFile server: {e}")

    async def upload(self, file_path: str) -> SimpleNamespace:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            server = await self._get_server(client)
            upload_url = f"https://{server}.gofile.io/uploadFile"

            try:
                with open(file_path, "rb") as f:
                    files = {"file": f}
                    response = await client.post(upload_url, files=files)
                
                response.raise_for_status()
                result = response.json()

                if result.get("status") == "ok":
                    return SimpleNamespace(**result["data"])
                else:
                    raise Exception(f"GoFile API returned an error: {result.get('status')}")

            except httpx.RequestError as e:
                raise Exception(f"Failed to upload file to GoFile: {e}")
