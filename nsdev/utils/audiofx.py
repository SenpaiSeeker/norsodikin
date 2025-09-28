import asyncio
import functools
import subprocess
from typing import Dict


class AudioFX:
    def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        call = functools.partial(func, *args, **kwargs)
        return loop.run_in_executor(None, call)

    def _apply_ffmpeg_filter(self, input_path: str, output_path: str, filter_str: str):
        command = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-af",
            filter_str,
            "-c:a",
            "libopus",
            output_path,
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")
        return output_path

    async def apply_effect(self, input_path: str, output_path: str, effect: str):
        effects: Dict[str, str] = {
            "chipmunk": "atempo=1.5,asetrate=44100*0.7",
            "robot": "atempo=0.8,asetrate=44100*0.6",
            "echo": "aecho=0.8:0.9:500:0.3",
            "reverse": "areverse",
        }
        filter_string = effects.get(effect.lower())
        if not filter_string:
            raise ValueError(f"Efek '{effect}' tidak valid. Pilihan: {', '.join(effects.keys())}")

        return await self._run_in_executor(self._apply_ffmpeg_filter, input_path, output_path, filter_string)
