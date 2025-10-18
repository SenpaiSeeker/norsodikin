import asyncio
import os
import shutil
import subprocess
from functools import partial
from pathlib import Path


class AudioSplitter:
    def __init__(self, output_path: str = "downloads/splitter_output"):
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)

    def _sync_separate(self, audio_file_path: str) -> dict:
        cmd = [
            "python3",
            "-m",
            "demucs",
            "--two-stems=vocals",
            "-o",
            str(self.output_path),
            str(audio_file_path),
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Demucs failed with error: {result.stderr}")
        
        model_name = "htdemucs"
        base_name = Path(audio_file_path).stem
        output_dir = self.output_path / model_name / base_name
        
        vocals_path = output_dir / "vocals.wav"
        no_vocals_path = output_dir / "no_vocals.wav"

        if not vocals_path.exists() or not no_vocals_path.exists():
            raise FileNotFoundError("Pemisahan gagal, file output tidak ditemukan.")
            
        return {
            "vocals": str(vocals_path),
            "instrumental": str(no_vocals_path),
            "output_dir": str(output_dir.parent)
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
