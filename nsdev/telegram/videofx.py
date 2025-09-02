import asyncio
import functools
import math
import random
import subprocess
from typing import List, Tuple

from PIL import Image, ImageFont, ImageDraw, ImageFilter

from ..utils.font_manager import FontManager


class VideoFX(FontManager):
    def __init__(self):
        super().__init__()
        self.SABER_PALETTE = {
            "fill": (255, 255, 255, 255),
            "core_glow": (230, 210, 255, 255),
            "outer_glow": (160, 70, 255, 255),
        }
        self.particles = []

    def _get_text_mask(self, text_lines, font, canvas_size, text_pos) -> Image.Image:
        mask = Image.new("L", canvas_size, 0)
        draw = ImageDraw.Draw(mask)
        current_y = text_pos[1]
        for line in text_lines:
            bbox = draw.textbbox((0, 0), line, font=font, stroke_width=6)
            line_w = bbox[2] - bbox[0]
            pos = (canvas_size[0] / 2 - line_w / 2, current_y)
            draw.text(pos, line, font=font, fill=255, stroke_width=6, stroke_fill=255)
            current_y += bbox[3] - bbox[1] + 20
        return mask

    def _manage_particles(self, draw: ImageDraw.Draw, text_bbox: Tuple, canvas_size: Tuple):
        self.particles = [p for p in self.particles if p["life"] > 0]
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            alpha = int(255 * (p["life"] / p["max_life"]))
            color = (255, 255, 255, alpha)
            draw.point((p["x"], p["y"]), fill=color)

        if len(self.particles) < 150:
            for _ in range(5):
                self.particles.append({
                    "x": random.uniform(text_bbox[0], text_bbox[2]),
                    "y": random.uniform(text_bbox[1], text_bbox[3]),
                    "vx": random.uniform(-0.5, 0.5), "vy": random.uniform(-0.5, 0.5),
                    "life": random.randint(20, 50), "max_life": 50,
                })

    async def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        call = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, call)

    def _make_frame_pil(
        self, t: float, duration: float, text_lines: List[str], text_widths: List[float],
        text_heights: List[float], canvas_w: int, canvas_h: int, total_text_h: float, font: ImageFont.ImageFont
    ) -> Image.Image:
        
        base = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        outline_layer = Image.new("RGBA", canvas_w, (0, 0, 0, 0))
        draw_outline = ImageDraw.Draw(outline_layer)

        text_block_w = max(text_widths) if text_widths else 0
        text_block_x = (canvas_w - text_block_w) / 2
        text_block_y = (canvas_h - total_text_h) / 2
        
        current_y = text_block_y
        for i, line in enumerate(text_lines):
            line_w = text_widths[i]
            position = (text_block_x, current_y)
            
            for _ in range(5):
                jitter_x = random.uniform(-2, 2)
                jitter_y = random.uniform(-2, 2)
                draw_outline.text(
                    (position[0] + jitter_x, position[1] + jitter_y),
                    line, font=font, fill=self.SABER_PALETTE["core_glow"],
                    stroke_width=6, stroke_fill=self.SABER_PALETTE["core_glow"]
                )
            current_y += text_heights[i] + 20

        outer_glow = outline_layer.filter(ImageFilter.GaussianBlur(radius=20))
        solid_outer_glow = Image.new("RGBA", canvas_w, self.SABER_PALETTE["outer_glow"])
        solid_outer_glow.putalpha(outer_glow.getchannel("A"))

        inner_glow = outline_layer.filter(ImageFilter.GaussianBlur(radius=8))

        base = Image.alpha_composite(base, solid_outer_glow)
        base = Image.alpha_composite(base, inner_glow)
        
        draw_base = ImageDraw.Draw(base)
        current_y = text_block_y
        for i, line in enumerate(text_lines):
            line_w = text_widths[i]
            position = (text_block_x, current_y)
            draw_base.text(position, line, font=font, fill=self.SABER_PALETTE["fill"])
            current_y += text_heights[i] + 20

        reveal_duration = 1.5
        reveal_progress = min(1.0, t / reveal_duration)
        if reveal_progress < 1.0:
            reveal_mask = Image.new("L", (canvas_w, canvas_h), 0)
            draw_mask = ImageDraw.Draw(reveal_mask)
            reveal_width = canvas_w * reveal_progress
            draw_mask.rectangle([0, 0, reveal_width, canvas_h], fill=255)
            reveal_mask = reveal_mask.filter(ImageFilter.GaussianBlur(radius=15))
            base.putalpha(reveal_mask)

        text_bbox = (text_block_x, text_block_y, text_block_x + text_block_w, text_block_y + total_text_h)
        self._manage_particles(draw_base, text_bbox, (canvas_w, canvas_h))

        return base

    def _create_saber_video(
        self, text_lines: List[str], output_path: str, duration: float, fps: int, font_size: int = 90
    ):
        text_lines = [t.strip() for t in text_lines if t and t.strip()]
        if not text_lines: text_lines = [" "]

        font = self._get_font(font_size)
        dummy_img = Image.new("RGBA", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)

        bboxes = [dummy_draw.textbbox((0, 0), line, font=font) for line in text_lines]
        text_widths = [bbox[2] - bbox[0] for bbox in bboxes]
        text_heights = [bbox[3] - bbox[1] for bbox in bboxes]

        base_w = max(max(text_widths) + 100, 512)
        canvas_w = base_w - (base_w % 2)
        total_text_h = sum(text_heights) + (len(text_lines) - 1) * 20
        base_h = max(total_text_h + 100, 512)
        canvas_h = base_h - (base_h % 2)
        
        self.particles = []

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
                t, duration, text_lines, text_widths, text_heights,
                canvas_w, canvas_h, total_text_h, font,
            )
            proc.stdin.write(frame_img.tobytes())

        _, stderr = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {stderr.decode(errors='ignore')}")

    async def text_to_video(
        self, text: str, output_path: str, duration: float = 5.0, fps: int = 24, font_size: int = 90
    ):
        text_lines = text.split(";") if ";" in text else text.splitlines()
        await self._run_in_executor(
            self._create_saber_video, text_lines, output_path, duration, fps, font_size
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
