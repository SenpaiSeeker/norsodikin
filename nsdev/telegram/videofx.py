import asyncio
import functools
import math
import random
import subprocess
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFilter

from ..utils.font_manager import FontManager


class VideoFX(FontManager):
    def __init__(self):
        super().__init__()

    def _generate_jagged_path(
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

    def _draw_lightning_bolt(self, canvas_size: Tuple, text_bbox: Tuple) -> Image.Image:
        effect_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        draw_effect = ImageDraw.Draw(effect_layer)

        start_x = random.uniform(text_bbox[0] - 20, text_bbox[2] + 20)
        start_y = random.uniform(text_bbox[1] - 20, text_bbox[3] + 20)
        end_x = random.choice([random.uniform(-50, 0), random.uniform(canvas_size[0], canvas_size[0] + 50)])
        end_y = random.choice([random.uniform(0, canvas_size[1])])

        main_path = self._generate_jagged_path((start_x, start_y), (end_x, end_y), 25, 12)
        draw_effect.line(main_path, fill=(200, 255, 255, 180), width=4, joint="round")
        draw_effect.line(main_path, fill=(255, 255, 255, 255), width=2, joint="round")

        if random.random() < 0.7:
            branch_start_index = random.randint(3, len(main_path) - 4)
            branch_start_point = main_path[branch_start_index]
            branch_end_x = branch_start_point[0] + random.uniform(-150, 150)
            branch_end_y = branch_start_point[1] + random.uniform(-150, 150)
            branch_path = self._generate_jagged_path(branch_start_point, (branch_end_x, branch_end_y), 15, 8)
            draw_effect.line(branch_path, fill=(200, 255, 255, 150), width=3, joint="round")

        aura_layer = effect_layer.filter(ImageFilter.GaussianBlur(radius=8))
        aura_color = (100, 200, 255)
        solid_color_aura = Image.new("RGBA", canvas_size, aura_color + (0,))
        aura_mask = aura_layer.getchannel("A")
        solid_color_aura.putalpha(aura_mask)
        
        final_effect_layer = Image.alpha_composite(solid_color_aura, effect_layer)
        return final_effect_layer

    async def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        call = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, call)

    def _make_frame_pil(self, t: float, state: Dict) -> Image.Image:
        canvas_w, canvas_h = state["canvas_size"]
        base = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

        if random.random() < 0.08 and state["flash_intensity"] <= 0.1:
            state["flash_intensity"] = 200.0
            state["lightning_layer"] = self._draw_lightning_bolt(base.size, state["text_bbox"])
        else:
            state["lightning_layer"] = None

        if state["lightning_layer"]:
            base = Image.alpha_composite(base, state["lightning_layer"])

        draw_base = ImageDraw.Draw(base)
        font = state["font"]

        r = int(127 * (1 + math.sin(t * 5 + 0))) + 128
        g = int(127 * (1 + math.sin(t * 5 + 2))) + 128
        b = int(127 * (1 + math.sin(t * 5 + 4))) + 128
        text_color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
        shadow_color = tuple(int(c * 0.4) for c in text_color)

        current_y = state["text_bbox"][1]
        for i, line in enumerate(state["text_lines"]):
            line_w = state["text_widths"][i]
            pos_x = (canvas_w - line_w) / 2
            pos_y = current_y
            draw_base.text((pos_x + 3, pos_y + 3), line, font=font, fill=shadow_color)
            draw_base.text((pos_x, pos_y), line, font=font, fill=text_color)
            current_y += state["text_heights"][i] + 20

        if state["flash_intensity"] > 0:
            flash_alpha = int(state["flash_intensity"])
            flash_layer = Image.new("RGBA", base.size, (255, 255, 255, flash_alpha))
            base = Image.alpha_composite(base, flash_layer)
            state["flash_intensity"] *= 0.6

        return base

    def _create_animated_video(
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

        state = {
            "canvas_size": (canvas_w, canvas_h),
            "font": font,
            "text_lines": text_lines,
            "text_widths": text_widths,
            "text_heights": text_heights,
            "text_bbox": (
                (canvas_w - max(text_widths)) / 2,
                (canvas_h - total_text_h) / 2,
                (canvas_w + max(text_widths)) / 2,
                (canvas_h + total_text_h) / 2,
            ),
            "flash_intensity": 0.0,
            "lightning_layer": None,
        }

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
            frame_img = self._make_frame_pil(t, state)
            proc.stdin.write(frame_img.tobytes())

        _, stderr = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during video creation: {stderr.decode(errors='ignore')}")

    async def text_to_video(
        self,
        text: str,
        output_path: str,
        duration: float = 2.95,
        fps: int = 30,
        font_size: int = 90,
        **kwargs,
    ):
        text_lines = text.split(";") if ";" in text else text.splitlines()
        await self._run_in_executor(
            self._create_animated_video,
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
