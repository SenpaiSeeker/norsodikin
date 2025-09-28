from io import BytesIO

import httpx
from fake_useragent import UserAgent


class ZeroXZeroUploader:
    def __init__(self, timeout: int = 60):
        self.api_url = "https://0x0.st"
        self.timeout = timeout
        self.headers = {"User-Agent": UserAgent().random}

    async def upload(self, file_bytes: bytes, file_name: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                files = {'file': (file_name, BytesIO(file_bytes))}
                
                response = await client.post(self.api_url, files=files, headers=self.headers)
                response.raise_for_status()

                url = response.text.strip()
                if url.startswith("http"):
                    return url
                else:
                    raise Exception(f"API returned an invalid response: {url}")

            except httpx.RequestError as e:
                raise Exception(f"Failed to connect to 0x0.st API: {e}")
            except httpx.HTTPStatusError as e:
                raise Exception(f"0x0.st API returned an error: {e.response.status_code} - {e.response.text}")
