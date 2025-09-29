from io import BytesIO
from types import SimpleNamespace
from typing import List

import httpx

from ..utils.cache import memoize


class VoiceCloner:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key untuk ElevenLabs diperlukan.")
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"

    @memoize(ttl=3600)
    async def get_voices(self) -> List[SimpleNamespace]:
        url = f"{self.base_url}/voices"
        voices_list = []

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                for voice in data.get("voices", []):
                    labels = voice.get("labels", {})
                    description_parts = [
                        labels.get(key) for key in ["accent", "gender", "description", "age"] if labels.get(key)
                    ]
                    description = ", ".join(description_parts).title()
                    
                    voices_list.append(
                        SimpleNamespace(
                            id=voice.get("voice_id"),
                            name=voice.get("name"),
                            description=description or "No description",
                        )
                    )
                return voices_list
            except Exception as e:
                raise Exception(f"Gagal mengambil daftar suara dari ElevenLabs: {e}")


    async def clone(self, text: str, voice_id: str) -> BytesIO:
        url = f"{self.base_url}/text-to-speech/{voice_id}"
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
