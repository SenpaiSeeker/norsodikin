import asyncio
import json
import subprocess
from functools import partial
from types import SimpleNamespace


class MediaInspector:
    def _format_duration(self, seconds_str: str) -> str:
        seconds = float(seconds_str)
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

    def _format_bitrate(self, bitrate_str: str) -> str:
        bitrate = int(bitrate_str)
        return f"{bitrate / 1000:.0f} kb/s"

    def _sync_get_media_info(self, file_path: str) -> SimpleNamespace:
        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path,
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {result.stderr}")
        
        data = json.loads(result.stdout)
        info = SimpleNamespace(video=None, audio=None, general=None)

        # General format info
        if "format" in data:
            fmt = data["format"]
            info.general = SimpleNamespace(
                duration=self._format_duration(fmt.get("duration", "0")),
                bitrate=self._format_bitrate(fmt.get("bit_rate", "0")),
                format_name=fmt.get("format_long_name", "N/A"),
            )
        
        # Stream info
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video" and not info.video:
                info.video = SimpleNamespace(
                    codec=stream.get("codec_name", "N/A"),
                    resolution=f"{stream.get('width')}x{stream.get('height')}",
                    fps=eval(stream.get("avg_frame_rate", "0/1")),
                    bitrate=self._format_bitrate(stream.get("bit_rate", "0")),
                )
            elif stream.get("codec_type") == "audio" and not info.audio:
                info.audio = SimpleNamespace(
                    codec=stream.get("codec_name", "N/A"),
                    sample_rate=f"{stream.get('sample_rate')} Hz",
                    channels=stream.get("channel_layout", "N/A"),
                    bitrate=self._format_bitrate(stream.get("bit_rate", "0")),
                )
        
        return info

    async def get_info(self, file_path: str) -> SimpleNamespace:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._sync_get_media_info, file_path))
