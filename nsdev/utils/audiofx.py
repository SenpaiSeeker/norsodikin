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
            "-b:a",
            "32k",
            output_path,
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")
        return output_path

    async def apply_effect(self, input_path: str, output_path: str, effect: str):
        effects: Dict[str, str] = {
            "chipmunk": "rubberband=pitch=1.5",
            "deep": "rubberband=pitch=0.7",
            "robot": "afftfilt=real='hypot(re,im)*cos(0)':imag='hypot(re,im)*sin(0)'",
            "echo": "aecho=0.6:0.6:1000:0.4",
            "reverse": "areverse",
            "slow": "atempo=0.6",
            "fast": "atempo=1.8",
            "whisper": "volume=0.3,highpass=f=200,lowpass=f=3000,anequalizer=f=1000:t=q:w=2:g=-10",
        }
        filter_string = effects.get(effect.lower())
        if not filter_string:
            raise ValueError(f"Efek '{effect}' tidak valid. Pilihan: {', '.join(effects.keys())}")

        return await self._run_in_executor(self._apply_ffmpeg_filter, input_path, output_path, filter_string)
