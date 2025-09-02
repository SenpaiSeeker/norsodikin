import asyncio
import functools
import math
import random
import subprocess
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFilter

from ..utils.font_manager import FontManager

class Particle:
    def __init__(self, canvas_size: Tuple[int, int]):
        self.canvas_size = canvas_size
        self.reset()

    def reset(self):
        self.x = random.uniform(0, self.canvas_size[0])
        self.y = random.uniform(0, self.canvas_size[1])
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)
        self.life = random.randint(50, 150)
        self.max_life = self.life
        self.size = random.uniform(1, 3)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0:
            self.reset()

    def draw(self, draw: ImageDraw.Draw):
        alpha = int(255 * (self.life / self.max_life))
        color = (200, 180, 255, alpha)
        draw.ellipse([self.x, self.y, self.x + self.size, self.y + self.size], fill=color)


class VideoFX(FontManager):
    def __init__(self):
        super().__init__()
        self.SABER_PALETTE = {
            "text_fill": (255, 255, 255, 255),
            "aura": (200, 150, 255),
        }

    async def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        call = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, call)

    def _make_frame_pil(
        self, t: float, duration: float, text_lines: List[str], text_pos: List[Tuple], font,
        canvas_size: Tuple[int, int], particles: List[Particle]
    ) -> Image.Image:
        base = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        
        particle_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        draw_particles = ImageDraw.Draw(particle_layer)
        for p in particles:
            p.update()
            p.draw(draw_particles)
        
        outline_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        draw_outline = ImageDraw.Draw(outline_layer)
        for i, line in enumerate(text_lines):
            draw_outline.text(text_pos[i], line, font=font, fill=(255, 255, 255, 255),
                              stroke_width=6, stroke_fill=(255, 255, 255, 255))
        
        flicker = (math.sin(t * 15) + math.sin(t * 23) + math.sin(t * 8)) / 3.0
        blur_radius = 12 + flicker * 4
        aura_layer = outline_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        solid_aura_color = Image.new("RGBA", canvas_size, self.SABER_PALETTE["aura"])
        aura_mask = aura_layer.getchannel("A")
        
        base.paste(particle_layer, (0, 0), particle_layer)
        base.paste(solid_aura_color, (0, 0), aura_mask)
        
        draw_text = ImageDraw.Draw(base)
        for i, line in enumerate(text_lines):
            draw_text.text(text_pos[i], line, font=font, fill=self.SABER_PALETTE["text_fill"])

        reveal_time = 0.8
        if t < reveal_time:
            reveal_factor = t / reveal_time
            alpha = base.getchannel("A")
            new_alpha = alpha.point(lambda p: int(p * reveal_factor))
            base.putalpha(new_alpha)

        return base

    def _create_rgb_video(
        self, text_lines: List[str], output_path: str, duration: float, fps: int, font_size: int
    ):
        text_lines = [line.strip() for line in text_lines if line and line.strip()]
        if not text_lines: text_lines = [" "]

        font = self._get_font(font_size)
        dummy_img = Image.new("RGBA", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)

        bboxes = [dummy_draw.textbbox((0, 0), line, font=font, stroke_width=6) for line in text_lines]
        text_widths = [bbox[2] - bbox[0] for bbox in bboxes]
        text_heights = [bbox[3] - bbox[1] for bbox in bboxes]

        canvas_w = max(max(text_widths) + 80, 512)
        canvas_w -= canvas_w % 2

        total_text_h = sum(text_heights) + (len(text_lines) - 1) * 20
        canvas_h = max(total_text_h + 80, 512)
        canvas_h -= canvas_h % 2

        text_pos = []
        current_y = (canvas_h - total_text_h) / 2
        for i, line in enumerate(text_lines):
            text_pos.append(((canvas_w - text_widths[i]) / 2, current_y))
            current_y += text_heights[i] + 20

        particles = [Particle((canvas_w, canvas_h)) for _ in range(50)]

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
                t, duration, text_lines, text_pos, font, (canvas_w, canvas_h), particles
            )
            proc.stdin.write(frame_img.tobytes())

        _, stderr = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {stderr.decode(errors='ignore')}")

    async def text_to_video(
        self, text: str, output_path: str, duration: float = 5.0, fps: int = 24,
        blink: bool = True, blink_smooth: bool = True, font_size: int = 110, **kwargs
    ):
        text_lines = text.split(";") if ";" in text else text.splitlines()
        await self._run_in_executor(
            self._create_rgb_video, text_lines, output_path, duration, fps, font_size
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
