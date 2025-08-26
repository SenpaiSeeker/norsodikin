from urllib import parse

import httpx


class UrlUtils:
    async def shorten(self, long_url: str):
        api_url = f"http://tinyurl.com/api-create.php?url={parse.quote(long_url)}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(api_url)
                response.raise_for_status()
                return response.text
            except httpx.RequestError as e:
                raise Exception(f"Gagal menghubungi layanan pemendek URL: {e}")
