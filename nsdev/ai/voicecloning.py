from io import BytesIO

import httpx


class VoiceCloner:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key untuk ElevenLabs diperlukan.")
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1/text-to-speech"

    async def clone(self, text: str, voice_id: str) -> BytesIO:
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        
        url = f"{self.base_url}/{voice_id}"

        async with httpx.AsyncClient(timeout=120) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                audio_bytes = BytesIO(response.content)
                audio_bytes.name = "cloned_voice.ogg"
                return audio_bytes

            except httpx.HTTPStatusError as e:
                error_body = e.response.json()
                error_detail = error_body.get("detail", {}).get("message", e.response.text)
                raise Exception(f"API ElevenLabs error: {error_detail}")
            except Exception as e:
                raise Exception(f"Gagal mengkloning suara: {e}")
