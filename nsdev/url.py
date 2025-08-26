class UrlUtils:
    def __init__(self):
        self.httpx = __import__("httpx")
        self.urllib = __import__("urllib")

    async def shorten(self, long_url: str):
        api_url = f"http://tinyurl.com/api-create.php?url={self.urllib.parse.quote(long_url)}"
        async with self.httpx.AsyncClient() as client:
            try:
                response = await client.get(api_url)
                response.raise_for_status()
                return response.text
            except self.httpx.RequestError as e:
                raise Exception(f"Gagal menghubungi layanan pemendek URL: {e}")
