import asyncio
import os
import subprocess

class AudioVisualizer:
    async def _run_ffmpeg(self, command):
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {stderr.decode().strip()}")
        return stdout

    async def generate_waveform(self, audio_path: str, output_path: str, width: int = 1280, height: int = 720, color: str = "cyan", bg_color: str = "black"):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        filter_str = f"color=c={bg_color}:s={width}x{height}[bg];[0:a]showwaves=s={width}x{height}:mode=line:colors={color}:draw=full[fg];[bg][fg]overlay=format=auto[v]"

        command = [
            "ffmpeg",
            "-y",
            "-i", audio_path,
            "-filter_complex", filter_str,
            "-map", "[v]",
            "-map", "0:a",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_path
        ]

        await self._run_ffmpeg(command)
        return output_path

    async def generate_spectrum(self, audio_path: str, output_path: str, width: int = 1280, height: int = 720):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        filter_str = f"[0:a]showfreqs=s={width}x{height}:mode=bar:ascale=sqrt:fscale=log:colors=yellow|red|blue[v]"

        command = [
            "ffmpeg",
            "-y",
            "-i", audio_path,
            "-filter_complex", filter_str,
            "-map", "[v]",
            "-map", "0:a",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            output_path
        ]

        await self._run_ffmpeg(command)
        return output_path

    async def render_with_image(self, audio_path: str, image_path: str, output_path: str):
        if not os.path.exists(audio_path) or not os.path.exists(image_path):
            raise FileNotFoundError("Audio or Image file not found")

        filter_str = "[0:a]showwaves=s=1280x200:mode=line:colors=white:draw=full[wave];[1:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2[bg];[bg][wave]overlay=x=0:y=H-h-20[v]"

        command = [
            "ffmpeg",
            "-y",
            "-i", audio_path,
            "-i", image_path,
            "-filter_complex", filter_str,
            "-map", "[v]",
            "-map", "0:a",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_path
        ]

        await self._run_ffmpeg(command)
        return output_path
