from io import BytesIO
from types import SimpleNamespace
from typing import List, Optional
import os
import asyncio
from pathlib import Path

from gtts import gTTS
from pydub import AudioSegment

from ..utils.logger import LoggerHandler


class VoiceCloner:
    def __init__(self):
        self.logger = LoggerHandler()
        self.logger.info("VoiceCloner diinisialisasi dengan gTTS (unlimited, no API key needed)")
        
        self.voice_configs = {
            "male_id": {"lang": "id", "tld": "co.id", "slow": False},
            "female_id": {"lang": "id", "tld": "com", "slow": False},
            "male_en": {"lang": "en", "tld": "com", "slow": False},
            "female_en": {"lang": "en", "tld": "co.uk", "slow": False},
            "male_en_au": {"lang": "en", "tld": "com.au", "slow": False},
            "female_en_in": {"lang": "en", "tld": "co.in", "slow": False},
            "spanish": {"lang": "es", "tld": "com", "slow": False},
            "french": {"lang": "fr", "tld": "com", "slow": False},
            "german": {"lang": "de", "tld": "com", "slow": False},
            "italian": {"lang": "it", "tld": "com", "slow": False},
            "portuguese": {"lang": "pt", "tld": "com", "slow": False},
            "japanese": {"lang": "ja", "tld": "com", "slow": False},
            "korean": {"lang": "ko", "tld": "com", "slow": False},
            "chinese": {"lang": "zh-CN", "tld": "com", "slow": False},
            "arabic": {"lang": "ar", "tld": "com", "slow": False},
            "russian": {"lang": "ru", "tld": "com", "slow": False},
            "hindi": {"lang": "hi", "tld": "co.in", "slow": False},
            "thai": {"lang": "th", "tld": "com", "slow": False},
            "dutch": {"lang": "nl", "tld": "com", "slow": False},
            "polish": {"lang": "pl", "tld": "com", "slow": False},
        }

    async def get_voices(self) -> List[SimpleNamespace]:
        voices_list = [
            SimpleNamespace(
                id="male_id",
                name="Indonesian Male",
                description="Suara pria Indonesia natural"
            ),
            SimpleNamespace(
                id="female_id",
                name="Indonesian Female",
                description="Suara wanita Indonesia natural"
            ),
            SimpleNamespace(
                id="male_en",
                name="English Male (US)",
                description="Natural American English male voice"
            ),
            SimpleNamespace(
                id="female_en",
                name="English Female (UK)",
                description="Natural British English female voice"
            ),
            SimpleNamespace(
                id="male_en_au",
                name="English Male (Australian)",
                description="Natural Australian English male voice"
            ),
            SimpleNamespace(
                id="female_en_in",
                name="English Female (Indian)",
                description="Natural Indian English female voice"
            ),
            SimpleNamespace(
                id="spanish",
                name="Spanish",
                description="Natural Spanish voice"
            ),
            SimpleNamespace(
                id="french",
                name="French",
                description="Natural French voice"
            ),
            SimpleNamespace(
                id="german",
                name="German",
                description="Natural German voice"
            ),
            SimpleNamespace(
                id="japanese",
                name="Japanese",
                description="Natural Japanese voice"
            ),
            SimpleNamespace(
                id="korean",
                name="Korean",
                description="Natural Korean voice"
            ),
            SimpleNamespace(
                id="chinese",
                name="Chinese (Mandarin)",
                description="Natural Mandarin Chinese voice"
            ),
            SimpleNamespace(
                id="arabic",
                name="Arabic",
                description="Natural Arabic voice"
            ),
            SimpleNamespace(
                id="russian",
                name="Russian",
                description="Natural Russian voice"
            ),
            SimpleNamespace(
                id="hindi",
                name="Hindi",
                description="Natural Hindi voice"
            ),
        ]
        return voices_list

    async def clone(self, text: str, voice_id: str = "male_id", language: Optional[str] = None) -> BytesIO:
        if not text:
            raise ValueError("Text tidak boleh kosong")
        
        if len(text) > 1000000:
            self.logger.warning(f"Text panjang: {len(text)} karakter, tetap diproses (unlimited)")
        
        try:
            loop = asyncio.get_event_loop()
            audio_bytes = await loop.run_in_executor(None, self._generate_speech, text, voice_id, language)
            return audio_bytes
        except Exception as e:
            error_text = f"Gagal menghasilkan suara: {e}"
            self.logger.error(error_text)
            raise Exception(error_text)
    
    def _generate_speech(self, text: str, voice_id: str, language: Optional[str]) -> BytesIO:
        try:
            voice_config = self.voice_configs.get(voice_id, self.voice_configs["male_id"])
            
            if language:
                voice_config = voice_config.copy()
                voice_config["lang"] = language
            
            tts = gTTS(
                text=text,
                lang=voice_config["lang"],
                tld=voice_config["tld"],
                slow=voice_config["slow"]
            )
            
            temp_output = "/tmp/tts_output.mp3"
            tts.save(temp_output)
            
            with open(temp_output, "rb") as f:
                audio_data = f.read()
            
            audio_bytes = BytesIO(audio_data)
            audio_bytes.name = "cloned_voice.mp3"
            
            if os.path.exists(temp_output):
                os.remove(temp_output)
            
            self.logger.info(f"Audio berhasil dibuat: {len(audio_data)} bytes dengan voice: {voice_id}")
            return audio_bytes
            
        except Exception as e:
            error_text = f"Error saat generate speech: {e}"
            self.logger.error(error_text)
            raise Exception(error_text)
    
    async def clone_long_text(self, text: str, voice_id: str = "male_id", chunk_size: int = 5000) -> BytesIO:
        if len(text) <= chunk_size:
            return await self.clone(text, voice_id)
        
        try:
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            self.logger.info(f"Memproses {len(chunks)} chunk untuk text panjang")
            
            loop = asyncio.get_event_loop()
            audio_segments = []
            
            for i, chunk in enumerate(chunks):
                self.logger.info(f"Memproses chunk {i+1}/{len(chunks)}")
                audio_bytes = await loop.run_in_executor(None, self._generate_speech, chunk, voice_id, None)
                
                temp_file = f"/tmp/chunk_{i}.mp3"
                with open(temp_file, "wb") as f:
                    f.write(audio_bytes.getvalue())
                
                segment = AudioSegment.from_mp3(temp_file)
                audio_segments.append(segment)
                
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            combined = sum(audio_segments)
            
            output_path = "/tmp/combined_output.mp3"
            combined.export(output_path, format="mp3")
            
            with open(output_path, "rb") as f:
                final_audio = BytesIO(f.read())
            
            final_audio.name = "cloned_voice_long.mp3"
            
            if os.path.exists(output_path):
                os.remove(output_path)
            
            self.logger.info(f"Audio panjang berhasil digabungkan: {len(final_audio.getvalue())} bytes")
            return final_audio
            
        except Exception as e:
            error_text = f"Error saat generate long text: {e}"
            self.logger.error(error_text)
            raise Exception(error_text)
    
    def get_available_languages(self) -> List[str]:
        return ["id", "en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "ko", "hi", "th", "vi", "bn"]
    
    def get_available_voices(self) -> List[str]:
        return list(self.voice_configs.keys())
