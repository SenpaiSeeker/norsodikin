import base64

from .gemini import ChatbotGemini


class OCR(ChatbotGemini):
    def __init__(self, api_key: str):
        super().__init__(api_key)

    async def read_text(self, image_bytes: bytes) -> str:
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        
        prompt = (
            "Extract any and all text from this image. "
            "Do not add any explanation, formatting, or comments. "
            "Provide only the raw extracted text. If there is no text, return an empty response."
        )

        contents = [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": encoded_image}},
                ]
            }
        ]
        
        payload = {"contents": contents}
        return await self._send_request(**payload)
