import asyncio
import os
from functools import partial
from pathlib import Path
from spleeter.separator import Separator

class AudioSplitter:
    def __init__(self, output_path: str = "downloads/splitter_output"):
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.separator = Separator('spleeter:2stems')

    def _sync_separate(self, audio_file_path: str) -> dict:
        self.separator.separate_to_file(str(audio_file_path), str(self.output_path))
        
        base_name = Path(audio_file_path).stem
        output_dir = self.output_path / base_name
        
        vocals_path = output_dir / "vocals.wav"
        accompaniment_path = output_dir / "accompaniment.wav"

        if not vocals_path.exists() or not accompaniment_path.exists():
            raise FileNotFoundError("Pemisahan gagal, file output tidak ditemukan.")
            
        return {
            "vocals": str(vocals_path),
            "instrumental": str(accompaniment_path)
        }

    async def separate(self, audio_file_path: str) -> dict:
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                None, 
                partial(self._sync_separate, audio_file_path)
            )
            return result
        except Exception as e:
            raise RuntimeError(f"Gagal memisahkan audio: {e}")
