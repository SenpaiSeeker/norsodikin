import asyncio
import functools
import math
import random
import subprocess
from typing import List, Tuple, Dict

from PIL import Image, ImageDraw, ImageFilter

from ..utils.font_manager import FontManager


class LightningBolt:
    def __init__(self, start_pos: Tuple, end_pos: Tuple, creation_time: float):
        self.creation_time = creation_time
        self.lifetime = random.uniform(0.25, 0.5)
        self.branches: List[List[Tuple]] = []
        self._build_tree(start_pos, end_pos, max_offset=40, segments=15, depth=0)

    def _build_tree(self, start_pos, end_pos, max_offset, segments, depth):
        if depth > 4:
            return

        path = self._generate_path(start_pos, end_pos, max_offset, segments)
        self.branches.append(path)

        num_branches = random.randint(0, 3 if depth < 2 else 1)
        for _ in range(num_branches):
            if len(path) > 4:
                branch_start_index = random.randint(2, len(path) - 3)
                branch_start_point = path[branch_start_index]
                
                angle = math.atan2(end_pos[1] - start_pos[1], end_pos[0] - start_pos[0])
                branch_angle = angle + random.uniform(-math.pi / 2, math.pi / 2)
                branch_length = random.uniform(50, 150) / (depth + 1)

                branch_end_x = branch_start_point[0] + branch_length * math.cos(branch_angle)
                branch_end_y = branch_start_point[1] + branch_length * math.sin(branch_angle)
                
                self._build_tree(
                    branch_start_point, (branch_end_x, branch_end_y),
                    max_offset * 0.6, segments=10, depth=depth + 1
                )

    def _generate_path(self, start_pos, end_pos, max_offset, segments):
        points = [start_pos]
        dx, dy = end_pos[0] - start_pos[0], end_pos[1] - start_pos[1]
        length = math.hypot(dx, dy)
        if length == 0: return [start_pos, end_pos]
        
        for i in range(1, segments):
            progress = i / segments
            base_x = start_pos[0] + dx * progress
            base_y = start_pos[1] + dy * progress
            offset = random.uniform(-max_offset, max_offset) * (1 - abs(i/segments * 2 - 1))
            points.append((base_x + offset * (-dy / length), base_y + offset * (dx / length)))
        points.append(end_pos)
        return points

    def is_alive(self, current_time: float) -> bool:
        return current_time - self.creation_time < self.lifetime

    def draw(self, current_time: float, canvas_size: Tuple) -> Image.Image:
        age = (current_time - self.creation_time) / self.lifetime
        brightness = math.sin(age * math.pi) * (1 + random.uniform(-0.2, 0.2))
        
        core_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        draw_core = ImageDraw.Draw(core_layer)

        for branch_path in self.branches:
            jittered_path = [(p[0] + random.uniform(-1, 1), p[1] + random.uniform(-1, 1)) for p in branch_path]
            
            draw_core.line(jittered_path, fill=(255, 200, 255, int(255 * brightness)), width=4, joint="round")
            draw_core.line(jittered_path, fill=(255, 255, 255, int(255 * brightness)), width=2, joint="round")

        aura_outer = core_layer.filter(ImageFilter.GaussianBlur(radius=12))
        solid_aura_outer = Image.new("RGBA", canvas_size, (80, 40, 150, 0))
        solid_aura_outer.putalpha(aura_outer.getchannel("A"))

        aura_inner = core_layer.filter(ImageFilter.GaussianBlur(radius=5))
        solid_aura_inner = Image.new("RGBA", canvas_size, (180, 100, 255, 0))
        solid_aura_inner.putalpha(aura_inner.getchannel("A"))

        final_bolt = Image.alpha_composite(solid_aura_outer, solid_aura_inner)
        final_bolt = Image.alpha_composite(final_bolt, core_layer)
        return final_bolt


class VideoFX(FontManager):
    def __init__(self):
        super().__init__()
        self.active_bolts: List[LightningBolt] = []

    async def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        call = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, call)

    def _make_frame_pil(
        self, t: float, text_lines: List[str], text_widths: List[float],
        text_heights: List[float], canvas_w: int, canvas_h: int,
        total_text_h: float, font
    ) -> Image.Image:
        base = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

        self.active_bolts = [b for b in self.active_bolts if b.is_alive(t)]

        if random.random() < 0.15 and len(self.active_bolts) < 3:
            text_block_w = max(text_widths) if text_widths else 0
            text_block_x = (canvas_w - text_block_w) / 2
            text_block_y = (canvas_h - total_text_h) / 2
            
            start_x = random.uniform(text_block_x - 50, text_block_x + text_block_w + 50)
            start_y = random.uniform(text_block_y - 50, text_block_y + total_text_h + 50)
            end_x = random.choice([random.uniform(-100, 0), random.uniform(canvas_w, canvas_w + 100)])
            end_y = random.choice([random.uniform(-100, 0), random.uniform(canvas_h, canvas_h + 100)])
            
            self.active_bolts.append(LightningBolt((start_x, start_y), (end_x, end_y), t))

        for bolt in self.active_bolts:
            bolt_img = bolt.draw(t, (canvas_w, canvas_h))
            base = Image.alpha_composite(base, bolt_img)

        draw_base = ImageDraw.Draw(base)
        
        r = int(127 * (1 + math.sin(t * 5 + 0))) + 64
        g = int(127 * (1 + math.sin(t * 5 + 2))) + 64
        b = int(127 * (1 + math.sin(t * 5 + 4))) + 64
        intensity = 0.5 * (1 + math.sin(2 * math.pi * 2.0 * t - math.pi / 2))
        intensity = max(0.0, min(1.0, intensity))
        fill_color = (int(r * intensity), int(g * intensity), int(b * intensity), int(255 * intensity))

        current_y = (canvas_h - total_text_h) / 2
        for i, line in enumerate(text_lines):
            line_w = text_widths[i]
            position = ((canvas_w - line_w) / 2, current_y)
            draw_base.text(position, line, font=font, fill=fill_color)
            current_y += text_heights[i] + 20

        return base

    def _create_rgb_video(
        self, text_lines: List[str], output_path: str, duration: float, fps: int, font_size: int
    ):
        self.active_bolts = []
        text_lines = [line.strip() for line in text_lines if line and line.strip()] or [" "]

        font = self._get_font(font_size)
        dummy_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        
        bboxes = [dummy_draw.textbbox((0, 0), line, font=font) for line in text_lines]
        text_widths = [bbox[2] - bbox[0] for bbox in bboxes]
        text_heights = [bbox[3] - bbox[1] for bbox in bboxes]

        base_w = max(max(text_widths) + 80, 512)
        canvas_w = base_w - (base_w % 2)
        total_text_h = sum(text_heights) + (len(text_lines) - 1) * 20
        base_h = max(total_text_h + 80, 512)
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
                canvas_w, canvas_h, total_text_h, font
            )
            proc.stdin.write(frame_img.tobytes())

        _, stderr = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during video creation: {stderr.decode(errors='ignore')}")

    async def text_to_video(
        self, text: str, output_path: str, duration: float = 5.0,
        fps: int = 24, font_size: int = 90, **kwargs
    ):
        text_lines = text.split(";") if ";" in text else text.splitlines()
        await self._run_in_executor(
            self._create_rgb_video,
            text_lines, output_path, duration, fps, font_size,
        )
        return output_path

    def _convert_to_sticker(self, video_path: str, output_path: str, fps: int = 30):
        try:
            ffprobe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
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
