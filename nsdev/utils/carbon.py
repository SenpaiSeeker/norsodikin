import httpx


class CarbonClient:
    def ____init____(self, timeout: int = 30):
        self.api_url = "https://carbonara.solopov.dev/api/cook"
        self.timeout = timeout

    async def generate(self, code: str) -> bytes:
        payload = {"code": code}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.api_url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                return response.content
            except httpx.RequestError as e:
                raise Exception(f"Failed to connect to Carbon API: {e}")
            except httpx.HTTPStatusError as e:
                raise Exception(f"Carbon API returned an error: {e.response.status_code} - {e.response.text}")
