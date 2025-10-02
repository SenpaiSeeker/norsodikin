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
            "chipmunk": "asetrate=44100*1.5,atempo=1.25,aresample=44100",
            "robot": "afftfilt=real='hypot(re,im)*cos(0)':imag='hypot(re,im)*sin(0)'",
            "echo": "aecho=0.8:0.9:1000:0.4",
            "reverse": "areverse",
            "slow": "atempo=0.7",
            "fast": "atempo=1.5",
            "deep": "asetrate=44100*0.75,atempo=1.1,aresample=44100",
            "whisper": "volume=0.3,highpass=f=300,lowpass=f=3000,afftfilt=real='random(0)':imag='random(1)'",
        }
        filter_string = effects.get(effect.lower())
        if not filter_string:
            raise ValueError(f"Efek '{effect}' tidak valid. Pilihan: {', '.join(effects.keys())}")

        return await self._run_in_executor(self._apply_ffmpeg_filter, input_path, output_path, filter_string)
