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
        self.FIRE_PALETTE = {
            "core": [(255, 255, 230, 255), (255, 245, 200, 255)],
            "inner_glow": [(255, 200, 0, 255)],
            "outer_glow": [(255, 100, 0, 255), (200, 50, 0, 255)],
        }

    def _generate_lightning_path(
        self, start_pos: Tuple, end_pos: Tuple, max_offset: float, segments: int
    ) -> List[Tuple]:
        points = [start_pos]
        dx, dy = end_pos[0] - start_pos[0], end_pos[1] - start_pos[1]
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            return [start_pos, end_pos]

        for i in range(1, segments):
            progress = i / segments
            base_x = start_pos[0] + dx * progress
            base_y = start_pos[1] + dy * progress
            offset = random.uniform(-max_offset, max_offset) * (1 - abs(progress - 0.5) * 2)
            points.append((base_x + offset * (-dy / length), base_y + offset * (dx / length)))
        points.append(end_pos)
        return points

    def _create_bolt_recursively(
        self, draw: ImageDraw, start: Tuple, end: Tuple, generations_left: int, initial_width: float, max_offset: float
    ):
        if generations_left <= 0 or initial_width < 1:
            return

        path = self._generate_lightning_path(start, end, max_offset, 15)
        
        width = int(initial_width)
        draw.line(path, fill=random.choice(self.FIRE_PALETTE["core"]), width=width, joint="round")
        if width > 2:
            draw.line(path, fill=random.choice(self.FIRE_PALETTE["core"]), width=max(1, width-2), joint="round")

        num_branches = random.randint(0, 3 if generations_left > 1 else 1)
        for _ in range(num_branches):
            if random.random() < 0.7:
                branch_start_point = random.choice(path[1:-2])
                angle = math.atan2(end[1] - start[1], end[0] - start[0]) + random.uniform(-1.5, 1.5)
                branch_length = math.dist(start, end) * random.uniform(0.4, 0.7)
                branch_end_point = (
                    branch_start_point[0] + branch_length * math.cos(angle),
                    branch_start_point[1] + branch_length * math.sin(angle),
                )
                self._create_bolt_recursively(
                    draw, branch_start_point, branch_end_point,
                    generations_left - 1, initial_width * 0.5, max_offset * 0.8
                )

    def _draw_fiery_lightning(self, canvas_img: Image.Image, text_bbox: Tuple) -> Image.Image:
        canvas_size = canvas_img.size
        core_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        draw_core = ImageDraw.Draw(core_layer)

        start_x = random.uniform(text_bbox[0] - 50, text_bbox[2] + 50)
        start_y = random.uniform(text_bbox[1] - 50, text_bbox[3] + 50)
        end_x = random.choice([random.uniform(-100, 0), random.uniform(canvas_size[0], canvas_size[0] + 100)])
        end_y = random.choice([random.uniform(-100, 0), random.uniform(canvas_size[1], canvas_size[1] + 100)])

        self._create_bolt_recursively(draw_core, (start_x, start_y), (end_x, end_y), generations_left=2, initial_width=8, max_offset=45)

        aura_wide = core_layer.filter(ImageFilter.GaussianBlur(radius=25))
        solid_aura_wide = Image.new("RGBA", canvas_size, random.choice(self.FIRE_PALETTE["outer_glow"]))
        solid_aura_wide.putalpha(aura_wide.getchannel("A"))

        aura_tight = core_layer.filter(ImageFilter.GaussianBlur(radius=10))
        solid_aura_tight = Image.new("RGBA", canvas_size, random.choice(self.FIRE_PALETTE["inner_glow"]))
        solid_aura_tight.putalpha(aura_tight.getchannel("A"))

        final_img = Image.alpha_composite(canvas_img, solid_aura_wide)
        final_img = Image.alpha_composite(final_img, solid_aura_tight)
        final_img = Image.alpha_composite(final_img, core_layer)
        return final_img

    async def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        call = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, call)

    def _make_frame_pil(
        self, t: float, text_lines: List[str], text_widths: List[float], text_heights: List[float],
        canvas_w: int, canvas_h: int, total_text_h: float, font,
        blink: bool, blink_rate: float, blink_smooth: bool,
    ) -> Image.Image:
        base = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        
        text_block_w = max(text_widths) if text_widths else 0
        text_block_x = (canvas_w - text_block_w) / 2
        text_block_y = (canvas_h - total_text_h) / 2
        text_bbox = (text_block_x, text_block_y, text_block_x + text_block_w, text_block_y + total_text_h)

        if random.random() < 0.4:
            base = self._draw_fiery_lightning(base, text_bbox)

        draw_base = ImageDraw.Draw(base)
        
        r, g, b = 255, int(180 + 75 * math.sin(t * 8)), 0
        intensity = 1.0
        if blink and blink_rate > 0:
            period = 1.0 / blink_rate
            if blink_smooth:
                intensity = 0.6 + 0.4 * (math.sin(2 * math.pi * blink_rate * t - math.pi / 2))
            else:
                intensity = 1.0 if (t % period) < (period / 2) else 0.5

        fill_color = (int(r * intensity), int(g * intensity), int(b * intensity), 255)

        current_y = text_block_y
        for i, line in enumerate(text_lines):
            line_w = text_widths[i]
            position = ((canvas_w - line_w) / 2, current_y)
            draw_base.text(position, line, font=font, fill=fill_color, stroke_width=2, stroke_fill=(0,0,0,180))
            current_y += text_heights[i] + 20

        return base

    def _create_rgb_video(
        self, text_lines: List[str], output_path: str, duration: float, fps: int,
        blink: bool = False, blink_rate: float = 2.0, blink_smooth: bool = False, font_size: int = 90
    ):
        text_lines = [t.strip() for t in text_lines if t and t.strip()]
        if not text_lines: text_lines = [" "]

        font = self._get_font(font_size)
        dummy_img = Image.new("RGBA", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)

        bboxes = [dummy_draw.textbbox((0, 0), line, font=font, stroke_width=2) for line in text_lines]
        text_widths = [bbox[2] - bbox[0] for bbox in bboxes]
        text_heights = [bbox[3] - bbox[1] for bbox in bboxes]

        base_w = max(max(text_widths) + 60, 512)
        canvas_w = base_w - (base_w % 2)

        total_text_h = sum(text_heights) + (len(text_lines) - 1) * 20
        base_h = max(total_text_h, 512)
        canvas_h = base_h - (base_h % 2)

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
                canvas_w, canvas_h, total_text_h, font,
                blink, blink_rate, blink_smooth,
            )
            proc.stdin.write(frame_img.tobytes())

        _, stderr = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {stderr.decode(errors='ignore')}")

    async def text_to_video(
        self, text: str, output_path: str, duration: float = 5.0, fps: int = 24,
        blink: bool = False, blink_rate: float = 2.0, blink_smooth: bool = False, font_size: int = 90
    ):
        text_lines = text.split(";") if ";" in text else text.splitlines()
        await self._run_in_executor(
            self._create_rgb_video, text_lines, output_path, duration, fps,
            blink=blink, blink_rate=blink_rate, blink_smooth=blink_smooth, font_size=font_size
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
