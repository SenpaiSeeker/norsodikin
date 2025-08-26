import httpx

class SpeechToText:
    def __init__(self, api_key: str, model_id: str = "openai/whisper-large-v3"):
        self.api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def transcribe(self, audio_bytes: bytes) -> str:
        async with httpx.AsyncClient(timeout=300) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    content=audio_bytes
                )
                response.raise_for_status()
                result = response.json()
                return result.get("text", "")
            except httpx.HTTPStatusError as e:
                error_details = e.response.json().get("error", str(e.response.text))
                raise Exception(f"Transcription failed: {e.response.status_code} - {error_details}")
            except Exception as e:
                raise Exception(f"An unexpected error occurred during transcription: {e}")
