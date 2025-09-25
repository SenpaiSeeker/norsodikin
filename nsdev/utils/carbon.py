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

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.api_url, json=payload, headers=headers, timeout=httpx.Timeout(self.timeout))
                response.raise_for_status()
                
                result = response.json()
                image_url = result.get("url")
                
                if not image_url:
                    raise Exception("API did not return an image URL.")
                
                image_response = await client.get(image_url, timeout=self.timeout)
                image_response.raise_for_status()
                
                return image_response.content

            except httpx.RequestError as e:
                raise Exception(f"Gagal terhubung ke API Carbon baru: {e}")
            except httpx.HTTPStatusError as e:
                raise Exception(f"API Carbon baru mengembalikan error: {e.response.status_code} - {e.response.text}")
