import httpx


class CarbonClient:
    def __init__(self, timeout: int = 30):
        self.api_url = "https://sourcecodeshots.com/api/image"
        self.timeout = timeout

    async def generate(self, code: str) -> bytes:
        payload = {
            "code": code,
            "language": "auto",
            "theme": "night-owl",
            "padding": 24,
            "show_line_numbers": False,
        }
        headers = {
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:
            try:
                response = await client.post(self.api_url, json=payload, headers=headers)
                response.raise_for_status()
                
                return response.content

            except httpx.RequestError as e:
                raise Exception(f"Gagal terhubung ke API Carbon: {e}")
            except httpx.HTTPStatusError as e:
                error_body = e.response.text
                raise Exception(f"API Carbon mengembalikan error: {e.response.status_code} - {error_body}")
