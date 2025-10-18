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
        cmd_mp3 = [
            "python3", 
            "-m", 
            "demucs",
            "--two-stems=vocals",
            "--mp3",
            "--mp3-bitrate=192",
            "-o",
            str(self.output_path),
            str(audio_file_path),
        ]
        
        result_mp3 = subprocess.run(cmd_mp3, capture_output=True, text=True)

        if result_mp3.returncode == 0:
            output_format = "mp3"
        else:
            cmd_wav = [
                "python3",
                "-m",
                "demucs",
                "--two-stems=vocals",
                "-o",
                str(self.output_path),
                str(audio_file_path),
            ]
            result_wav = subprocess.run(cmd_wav, capture_output=True, text=True)
            if result_wav.returncode != 0:
                error_log = result_mp3.stderr or result_wav.stderr
                raise RuntimeError(f"Demucs failed with error: {error_log}")
            output_format = "wav"

        model_name = "htdemucs"
        base_name = Path(audio_file_path).stem
        output_dir = self.output_path / model_name / base_name
        
        vocals_path = output_dir / f"vocals.{output_format}"
        no_vocals_path = output_dir / f"no_vocals.{output_format}"

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
