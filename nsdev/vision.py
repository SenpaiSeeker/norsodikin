import base64

import httpx


class VisionAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model = "gemini-1.5-flash-latest"

    async def _send_request(self, contents: list) -> str:
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": contents}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (httpx.HTTPStatusError, KeyError, IndexError) as e:
                raise Exception(f"API request failed: {e}\nResponse: {response.text}")
            except Exception as e:
                raise Exception(f"An unexpected error occurred: {e}")

    async def describe(self, image_bytes: bytes) -> str:
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        contents = [
            {
                "parts": [
                    {"text": "Deskripsikan gambar ini secara detail dalam bahasa Indonesia."},
                    {"inline_data": {"mime_type": "image/jpeg", "data": encoded_image}},
                ]
            }
        ]
        return await self._send_request(contents)

    async def ask(self, image_bytes: bytes, question: str) -> str:
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        contents = [
            {"parts": [{"text": question}, {"inline_data": {"mime_type": "image/jpeg", "data": encoded_image}}]}
        ]
        return await self._send_request(contents)
