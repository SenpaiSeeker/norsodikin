import base64

from .gemini import ChatbotGemini


class VisionAnalyzer(ChatbotGemini):
    def __init__(self, api_key: str):
        super().__init__(api_key)

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
        payload = {"contents": contents}
        return await self._send_request(**payload)

    async def ask(self, image_bytes: bytes, question: str) -> str:
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        contents = [
            {"parts": [{"text": question}, {"inline_data": {"mime_type": "image/jpeg", "data": encoded_image}}]}
        ]
        payload = {"contents": contents}
        return await self._send_request(**payload)
