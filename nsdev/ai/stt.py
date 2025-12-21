import httpx
import base64
from google import genai
from google.genai import types

class SpeechToText:
    def __init__(self, api_key: str, provider: str = "gemini", model_id: str = "openai/whisper-large-v3"):
        self.api_key = api_key
        self.provider = provider
        self.model_id = model_id
        
        if provider == "gemini":
            self.client = genai.Client(api_key=api_key)
        else:
            self.api_url = f"https://api-inference.huggingface.co/models/{model_id}"
            self.headers = {"Authorization": f"Bearer {api_key}"}

    async def transcribe(self, audio_bytes: bytes) -> str:
        if self.provider == "gemini":
            return await self._transcribe_gemini(audio_bytes)
        else:
            return await self._transcribe_hf(audio_bytes)

    async def _transcribe_hf(self, audio_bytes: bytes) -> str:
        request_headers = self.headers.copy()
        request_headers["Content-Type"] = "audio/ogg"

        async with httpx.AsyncClient(timeout=300) as client:
            try:
                response = await client.post(self.api_url, headers=request_headers, content=audio_bytes)
                response.raise_for_status()
                result = response.json()
                return result.get("text", "")
            except httpx.HTTPStatusError as e:
                raise Exception(f"Transcription failed: {e.response.status_code}")
            except Exception as e:
                raise Exception(f"Error: {e}")

    async def _transcribe_gemini(self, audio_bytes: bytes) -> str:
        encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")
        
        prompt = "Transcribe this audio file accurately. Return only the text."
        
        contents = [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "audio/ogg", "data": encoded_audio}},
                ]
            }
        ]
        
        try:
            config = types.GenerateContentConfig(response_mime_type="text/plain")
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash", 
                contents=contents,
                config=config
            )
            return response.text
        except Exception as e:
             try:
                 contents[0]["parts"][1]["inline_data"]["mime_type"] = "audio/mp3"
                 response = await self.client.aio.models.generate_content(
                    model="gemini-2.0-flash", 
                    contents=contents,
                    config=config
                )
                 return response.text
             except Exception as e2:
                raise Exception(f"Gemini STT failed: {e2}")
