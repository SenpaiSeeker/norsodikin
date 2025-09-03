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

    def _generate_lightning_path(
        self, start_pos: Tuple, end_pos: Tuple, max_offset: float, segments: int
    ) -> List[Tuple]:
        points = [start_pos]
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            return [start_pos, end_pos]

        for i in range(1, segments):
            progress = i / segments
            base_x = start_pos[0] + dx * progress
            base_y = start_pos[1] + dy * progress
            offset = random.uniform(-max_offset, max_offset)
            points.append((base_x + offset * (-dy / length), base_y + offset * (dx / length)))
        points.append(end_pos)
        return points

    def _draw_external_lightning(self, canvas_img: Image.Image, shield_bbox: Tuple) -> Image.Image:
        core_layer = Image.new("RGBA", canvas_img.size, (0, 0, 0, 0))
        draw_core = ImageDraw.Draw(core_layer)
        canvas_size = canvas_img.size

        start_x = random.uniform(shield_bbox[0], shield_bbox[2])
        start_y = random.uniform(shield_bbox[1], shield_bbox[3])
        end_x = random.choice([random.uniform(-50, 0), random.uniform(canvas_size[0], canvas_size[0] + 50)])
        end_y = random.choice([random.uniform(-50, 0), random.uniform(canvas_size[1], canvas_size[1] + 50)])

        main_path = self._generate_lightning_path((start_x, start_y), (end_x, end_y), 35, 15)

        draw_core.line(main_path, fill=(255, 255, 255, 220), width=4, joint="round")
        draw_core.line(main_path, fill=(255, 255, 238, 255), width=2, joint="round")

        if random.random() < 0.5:
            branch_start_index = random.randint(3, len(main_path) - 5)
            branch_start_point = main_path[branch_start_index]
            branch_end_x = branch_start_point[0] + random.uniform(-180, 180)
            branch_end_y = branch_start_point[1] + random.uniform(-180, 180)
            branch_path = self._generate_lightning_path(branch_start_point, (branch_end_x, branch_end_y), 20, 10)
            draw_core.line(branch_path, fill=(255, 255, 255, 180), width=3, joint="round")
            draw_core.line(branch_path, fill=(255, 255, 238, 255), width=1, joint="round")

        aura_layer = core_layer.filter(ImageFilter.GaussianBlur(radius=8))
        aura_color = (150, 180, 255)
        solid_color_aura = Image.new("RGBA", canvas_size, aura_color + (0,))
        aura_mask = aura_layer.getchannel("A")
        solid_color_aura.putalpha(aura_mask)

        final_img = Image.alpha_composite(canvas_img, solid_color_aura)
        final_img = Image.alpha_composite(final_img, core_layer)
        return final_img

    def _draw_extruded_text(self, draw, text, pos, font, fill_color, shadow_color, depth):
        x, y = pos
        for i in range(depth, 0, -1):
            draw.text((x + i, y + i), text, font=font, fill=shadow_color)
        draw.text(pos, text, font=font, fill=fill_color)

    async def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        call = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, call)

    def _make_frame_pil(
        self,
        t: float,
        text_lines: List[str],
        canvas_w: int,
        canvas_h: int,
        font,
        stars: List,
    ) -> Image.Image:
        base = Image.new("RGBA", (canvas_w, canvas_h), (20, 25, 40, 255))
        draw = ImageDraw.Draw(base)

        for x, y, size, phase, speed in stars:
            brightness = 0.5 * (1 + math.sin(t * speed + phase))
            alpha = int(brightness * 150) + 50
            draw.ellipse([x, y, x + size, y + size], fill=(180, 220, 255, alpha))

        text_bboxes = [draw.textbbox((0, 0), line, font=font) for line in text_lines]
        text_widths = [bbox[2] - bbox[0] for bbox in text_bboxes]
        text_heights = [bbox[3] - bbox[1] for bbox in text_bboxes]
        max_text_width = max(text_widths) if text_widths else 0
        total_text_height = sum(text_heights) + max(0, len(text_lines) - 1) * 20

        h_padding = max_text_width * 0.2
        v_padding = total_text_height * 0.4
        shield_w = max_text_width + h_padding
        shield_h = total_text_height + v_padding

        center_x, center_y = canvas_w / 2, canvas_h / 2
        
        shield_points = [
            (center_x - shield_w / 2, center_y - shield_h / 2.5),
            (center_x, center_y - shield_h / 2),
            (center_x + shield_w / 2, center_y - shield_h / 2.5),
            (center_x + shield_w / 2 * 0.9, center_y + shield_h / 2),
            (center_x, center_y + shield_h / 2 * 0.8),
            (center_x - shield_w / 2 * 0.9, center_y + shield_h / 2),
        ]
        
        r_outline = int(127 * (1 + math.sin(t * 4 + 2))) + 128
        g_outline = int(127 * (1 + math.sin(t * 4 + 4))) + 128
        b_outline = int(127 * (1 + math.sin(t * 4 + 0))) + 128
        shield_outline_color = (r_outline, g_outline, b_outline, 255)

        draw.polygon(shield_points, fill=(30, 30, 30, 255), outline=shield_outline_color, width=5)

        current_y = center_y - total_text_height / 2
        for i, line in enumerate(text_lines):
            line_w = text_widths[i]
            pos_x = center_x - line_w / 2
            self._draw_extruded_text(
                draw, line, (pos_x, current_y), font, (255, 200, 0), (180, 120, 0), depth=6
            )
            current_y += text_heights[i] + 20

        shield_bbox = (shield_points[0][0], shield_points[1][1], shield_points[2][0], shield_points[3][1])
        if random.random() < 0.3:
            base = self._draw_external_lightning(base, shield_bbox)

        return base

    def _create_rgb_video(
        self,
        text_lines: List[str],
        output_path: str,
        duration: float,
        fps: int,
        font_size: int = 90,
    ):
        text_lines = [t.strip() for t in text_lines if t and t.strip()]
        if not text_lines:
            text_lines = [" "]

        font = self._get_font(font_size)
        canvas_w, canvas_h = 512, 512

        stars = [
            (
                random.randint(0, canvas_w),
                random.randint(0, canvas_h),
                random.randint(1, 3),
                random.uniform(0, 2 * math.pi),
                random.uniform(2, 5),
            )
            for _ in range(100)
        ]

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
            frame_img = self._make_frame_pil(t, text_lines, canvas_w, canvas_h, font, stars)
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
        font_size: int = 90,
    ):
        text_lines = text.split(";") if ";" in text else text.splitlines()
        await self._run_in_executor(
            self._create_rgb_video, text_lines, output_path, duration, fps, font_size=font_size
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
