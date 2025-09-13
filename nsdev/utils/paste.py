import httpx


class PasteClient:
    def __init__(self, timeout: int = 15):
        self.post_url = "https://spaceb.in/"
        self.timeout = timeout

    async def paste(self, text: str, extension: str = "txt") -> str:
        payload = {
            "content": (None, text),
            "extension": (None, extension),
        }

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                response = await client.post(self.post_url, files=payload, timeout=self.timeout)
                response.raise_for_status()

                return str(response.url)

            except httpx.RequestError as e:
                raise Exception(f"Failed to connect to the paste service: {e}")
            except httpx.HTTPStatusError as e:
                raise Exception(f"The paste service returned an error: {e}")

