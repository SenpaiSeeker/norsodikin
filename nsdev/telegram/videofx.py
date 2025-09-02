import asyncio
import functools
import math
import random
import subprocess
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFilter

from ..utils.font_manager import FontManager


class VideoFX(FontManager):
    def __init__(self):
        super().__init__()

    def _generate_electric_spark_path(self, start_pos: Tuple) -> List[Tuple]:
        path = [start_pos]
        mid_point = (
            start_pos[0] + random.uniform(-8, 8),
            start_pos[1] + random.uniform(-8, 8),
        )
        end_point = (
            mid_point[0] + random.uniform(-8, 8),
            mid_point[1] + random.uniform(-8, 8),
        )
        path.extend([mid_point, end_point])
        return path

    def _get_text_boundary_points(
        self, text_lines, font, text_widths, text_heights, canvas_w, canvas_h, total_text_h
    ) -> List[Tuple[int, int]]:
        mask_img = Image.new("L", (canvas_w, canvas_h), 0)
        draw_mask = ImageDraw.Draw(mask_img)

        current_y = (canvas_h - total_text_h) / 2
        for i, line in enumerate(text_lines):
            line_w = text_widths[i]
            position = ((canvas_w - line_w) / 2, current_y)
            draw_mask.text(position, line, font=font, fill=255)
            current_y += text_heights[i] + 20

        pixels = mask_img.load()
        boundary_points = []
        for y in range(1, canvas_h - 1):
            for x in range(1, canvas_w - 1):
                if pixels[x, y] == 255:
                    if (
                        pixels[x + 1, y] == 0
                        or pixels[x - 1, y] == 0
                        or pixels[x, y + 1] == 0
                        or pixels[x, y - 1] == 0
                    ):
                        boundary_points.append((x, y))
        return boundary_points

    def _draw_electric_aura(
        self, canvas_img: Image.Image, boundary_points: List[Tuple[int, int]]
    ) -> Image.Image:
        if not boundary_points:
            return canvas_img

        core_layer = Image.new("RGBA", canvas_img.size, (0, 0, 0, 0))
        draw_core = ImageDraw.Draw(core_layer)

        num_sparks = int(len(boundary_points) * 0.35)
        spark_points = random.sample(boundary_points, min(num_sparks, len(boundary_points)))

        for point in spark_points:
            path = self._generate_electric_spark_path(point)
            draw_core.line(path, fill=(255, 255, 220, 200), width=2, joint="round")
            draw_core.line(path, fill=(255, 255, 255, 255), width=1, joint="round")

        aura_layer = core_layer.filter(ImageFilter.GaussianBlur(radius=5))
        aura_color_layer = Image.new("RGBA", canvas_img.size, (170, 220, 255, 0))
        aura_mask = aura_layer.getchannel("A")
        aura_color_layer.putalpha(aura_mask)

        final_img = Image.alpha_composite(canvas_img, aura_color_layer)
        final_img = Image.alpha_composite(final_img, core_layer)
        return final_img

    async def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        call = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, call)

    def _make_frame_pil(
        self,
        t: float,
        text_lines: List[str],
        text_widths: List[float],
        text_heights: List[float],
        canvas_w: int,
        canvas_h: int,
        total_text_h: float,
        font,
        boundary_points: List[Tuple[int, int]],
        blink: bool,
        blink_rate: float,
        blink_duty: float,
        blink_smooth: bool,
    ) -> Image.Image:
        base = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        
        base = self._draw_electric_aura(base, boundary_points)

        draw_base = ImageDraw.Draw(base)

        r = int(127 * (1 + math.sin(t * 5 + 0))) + 64
        g = int(127 * (1 + math.sin(t * 5 + 2))) + 64
        b = int(127 * (1 + math.sin(t * 5 + 4))) + 64

        intensity = 1.0
        if blink and blink_rate > 0:
            period = 1.0 / blink_rate
            on_duration = max(0.0, min(1.0, blink_duty)) * period
            if blink_smooth:
                intensity = 0.5 * (1 + math.sin(2 * math.pi * blink_rate * t - math.pi / 2))
                intensity = max(0.0, min(1.0, intensity))
            else:
                phase = t % period
                intensity = 1.0 if phase < on_duration else 0.0

        fill_color = (int(r * intensity), int(g * intensity), int(b * intensity), int(255 * intensity))

        current_y = (canvas_h - total_text_h) / 2
        for i, line in enumerate(text_lines):
            line_w = text_widths[i]
            position = ((canvas_w - line_w) / 2, current_y)
            draw_base.text(position, line, font=font, fill=fill_color)
            current_y += text_heights[i] + 20

        return base

    def _create_rgb_video(
        self,
        text_lines: List[str],
        output_path: str,
        duration: float,
        fps: int,
        blink: bool = False,
        blink_rate: float = 2.0,
        blink_duty: float = 0.15,
        blink_smooth: bool = False,
        font_size: int = 90,
    ):
        text_lines = [t.strip() for t in text_lines if t and t.strip()]
        if not text_lines:
            text_lines = [" "]

        font = self._get_font(font_size)
        dummy_img = Image.new("RGBA", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)

        bboxes = [dummy_draw.textbbox((0, 0), line, font=font) for line in text_lines]
        text_widths = [bbox[2] - bbox[0] for bbox in bboxes]
        text_heights = [bbox[3] - bbox[1] for bbox in bboxes]

        base_w = max(max(text_widths) + 80, 512)
        canvas_w = base_w - (base_w % 2)

        total_text_h = sum(text_heights) + (len(text_lines) - 1) * 20
        base_h = max(total_text_h + 80, 512)
        canvas_h = base_h - (base_h % 2)

        boundary_points = self._get_text_boundary_points(
            text_lines, font, text_widths, text_heights, canvas_w, canvas_h, total_text_h
        )

        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{canvas_w}x{canvas_h}", "-pix_fmt", "rgba",
            "-r", str(fps), "-i", "-", "-an", "-c:v", "png",
            "-preset", "fast", output_path,
        ]

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        num_frames = int(duration * fps)
        for i in range(num_frames):
            t = i / float(fps)
            frame_img = self._make_frame_pil(
                t, text_lines, text_widths, text_heights,
                canvas_w, canvas_h, total_text_h, font, boundary_points,
                blink, blink_rate, blink_duty, blink_smooth,
            )
            proc.stdin.write(frame_img.tobytes())

        _, stderr = proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during video creation: {stderr.decode(errors='ignore')}")

    async def text_to_video(
        self,
        text: str,
        output_path: str,
        duration: float = 5.0,
        fps: int = 24,
        blink: bool = False,
        blink_rate: float = 2.0,
        blink_duty: float = 0.15,
        blink_smooth: bool = False,
        font_size: int = 90,
    ):
        text_lines = text.split(";") if ";" in text else text.splitlines()
        await self._run_in_executor(
            self._create_rgb_video,
            text_lines, output_path, duration, fps,
            blink=blink, blink_rate=blink_rate, blink_duty=blink_duty,
            blink_smooth=blink_smooth, font_size=font_size,
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
