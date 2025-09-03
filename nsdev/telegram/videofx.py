import asyncio
import functools
import subprocess
from typing import List, Tuple

from PIL import Image, ImageDraw

from ..utils.font_manager import FontManager


class VideoFX(FontManager):
    def __init__(self):
        super().__init__()

    async def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        call = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, call)

    def _create_static_video_from_text(
        self,
        text_lines: List[str],
        output_path: str,
        duration: float,
        fps: int,
        font_size: int,
    ):
        text_lines = [t.strip() for t in text_lines if t and t.strip()] or [" "]
        font = self._get_font(font_size)
        dummy_img = Image.new("RGBA", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)

        bboxes = [dummy_draw.textbbox((0, 0), line, font=font) for line in text_lines]
        text_widths = [bbox[2] - bbox[0] for bbox in bboxes]
        text_heights = [bbox[3] - bbox[1] for bbox in bboxes]

        base_w = max(max(text_widths) + 80, 512)
        canvas_w = base_w - (base_w % 2)
        total_text_h = sum(text_heights) + (len(text_lines) - 1) * 20
        base_h = max(total_text_h, 512)
        canvas_h = base_h - (base_h % 2)

        static_frame = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(static_frame)

        text_color = (255, 255, 0)
        shadow_color = (50, 50, 0)

        current_y = (canvas_h - total_text_h) / 2
        for i, line in enumerate(text_lines):
            line_w = text_widths[i]
            pos_x = (canvas_w - line_w) / 2
            pos_y = current_y

            draw.text((pos_x + 4, pos_y + 4), line, font=font, fill=shadow_color)
            draw.text((pos_x, pos_y), line, font=font, fill=text_color)
            current_y += text_heights[i] + 20

        static_frame_bytes = static_frame.tobytes()

        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{canvas_w}x{canvas_h}", "-pix_fmt", "rgba",
            "-r", str(fps), "-i", "-", "-an", "-c:v", "png",
            "-preset", "fast", output_path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        num_frames = int(duration * fps)
        for _ in range(num_frames):
            proc.stdin.write(static_frame_bytes)

        _, stderr = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during video creation: {stderr.decode(errors='ignore')}")

    async def text_to_video(
        self,
        text: str,
        output_path: str,
        duration: float = 0.1,
        fps: int = 10,
        font_size: int = 90,
    ):
        text_lines = text.split(";") if ";" in text else text.splitlines()
        await self._run_in_executor(
            self._create_static_video_from_text,
            text_lines, output_path, duration, fps, font_size
        )
        return output_path

    def _convert_to_sticker(self, video_path: str, output_path: str, fps: int = 30):
        try:
            ffprobe_cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", video_path,
            ]
            result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            duration = 3.0

        trim_duration = min(duration, 2.95)
        scale_filter = "scale='if(gt(a,1),512,-2)':'if(gt(a,1),-2,512)'"

        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", video_path, "-t", str(trim_duration),
            "-vf", f"{scale_filter},fps={fps}", "-c:v", "libvpx-vp9",
            "-pix_fmt", "yuva420p", "-crf", "30", "-b:v", "0", "-an", output_path,
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during sticker conversion: {result.stderr}")

    async def video_to_sticker(self, video_path: str, output_path: str, fps: int = 30):
        await self._run_in_executor(self._convert_to_sticker, video_path, output_path, fps=fps)
        return output_path
