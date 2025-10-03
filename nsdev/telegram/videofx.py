import asyncio
import colorsys
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

    def _generate_jagged_path(self, start_pos: Tuple, end_pos: Tuple, max_offset: float, segments: int) -> List[Tuple]:
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

    def _draw_energy_cracks(self, canvas_size: Tuple, text_bbox: Tuple) -> Image.Image:
        core_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        draw_core = ImageDraw.Draw(core_layer)

        num_cracks = random.randint(3, 5)
        for _ in range(num_cracks):
            start_x = random.uniform(text_bbox[0], text_bbox[2])
            start_y = random.uniform(text_bbox[1], text_bbox[3])
            angle = random.uniform(0, 2 * math.pi)
            length = random.uniform(80, 150)
            end_x = start_x + length * math.cos(angle)
            end_y = start_y + length * math.sin(angle)

            path = self._generate_jagged_path((start_x, start_y), (end_x, end_y), 15, 10)
            draw_core.line(path, fill=(255, 255, 255, 200), width=3, joint="round")
            draw_core.line(path, fill=(220, 255, 255, 255), width=1, joint="round")

        aura_layer = core_layer.filter(ImageFilter.GaussianBlur(radius=12))
        aura_color = (100, 200, 255)
        solid_color_aura = Image.new("RGBA", canvas_size, aura_color + (0,))
        aura_mask = aura_layer.getchannel("A")
        solid_color_aura.putalpha(aura_mask)

        final_effect_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        final_effect_layer = Image.alpha_composite(final_effect_layer, solid_color_aura)
        final_effect_layer = Image.alpha_composite(final_effect_layer, core_layer)
        return final_effect_layer

    async def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        call = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, call)

    def _make_frame_pil(self, t: float, state: Dict) -> Image.Image:
        canvas_w, canvas_h = state["canvas_size"]
        base = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

        shake_intensity = state.get("shake_intensity", 0.0)
        shake_offset_x = random.uniform(-shake_intensity, shake_intensity)
        shake_offset_y = random.uniform(-shake_intensity, shake_intensity)
        state["shake_intensity"] *= state.get("shake_decay", 0.9)

        if random.random() < 0.15:
            state["shake_intensity"] = 10.0
            crack_layer = self._draw_energy_cracks(base.size, state["text_bbox"])
            base = Image.alpha_composite(base, crack_layer)

        draw_base = ImageDraw.Draw(base)
        font = state["font"]
        text_color = state["text_color"]
        shadow_color = state["shadow_color"]

        current_y = state["text_bbox"][1]
        for i, line in enumerate(state["text_lines"]):
            line_w = state["text_widths"][i]
            pos_x = ((canvas_w - line_w) / 2) + shake_offset_x
            pos_y = current_y + shake_offset_y

            draw_base.text((pos_x + 3, pos_y + 3), line, font=font, fill=shadow_color)
            draw_base.text((pos_x, pos_y), line, font=font, fill=text_color)
            current_y += state["text_heights"][i] + 20

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

        hue = random.random()
        rgb_float = colorsys.hsv_to_rgb(hue, 0.9, 1.0)
        text_color = tuple(int(c * 255) for c in rgb_float)
        shadow_color = tuple(int(c * 0.4) for c in text_color)

        state = {
            "canvas_size": (canvas_w, canvas_h),
            "font": font,
            "text_lines": text_lines,
            "text_widths": text_widths,
            "text_heights": text_heights,
            "text_color": text_color,
            "shadow_color": shadow_color,
            "text_bbox": (
                (canvas_w - max(text_widths)) / 2,
                (canvas_h - total_text_h) / 2,
                (canvas_w + max(text_widths)) / 2,
                (canvas_h + total_text_h) / 2,
            ),
            "shake_intensity": 0.0,
            "shake_decay": 0.92,
        }

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-s",
            f"{canvas_w}x{canvas_h}",
            "-pix_fmt",
            "rgba",
            "-r",
            str(fps),
            "-i",
            "-",
            "-an",
            "-c:v",
            "png",
            "-preset",
            "fast",
            output_path,
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
        fps: int = 60,
        font_size: int = 90,
    ):
        text_lines = text.split(";") if ";" in text else text.splitlines()
        await self._run_in_executor(self._create_animated_video, text_lines, output_path, duration, fps, font_size)
        return output_path

    def _sync_create_afk_animation(self, text_lines: List[str], output_path: str):
        font_main = self._get_font_from_package("NotoSans-Bold.ttf", 60)
        font_sub = self._get_font_from_package("NotoSans-Regular.ttf", 40)

        canvas_w, canvas_h = 512, 288
        img = Image.new("RGB", (canvas_w, canvas_h), "#181818")
        draw = ImageDraw.Draw(img)

        y_pos = 60
        for i, line in enumerate(text_lines):
            font = font_main if i == 0 else font_sub
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            line_h = bbox[3] - bbox[1]
            draw.text(((canvas_w - line_w) / 2, y_pos), line, font=font, fill="#FFFFFF")
            y_pos += line_h + 20

        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            "-",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-c:v",
            "libx264",
            "-t",
            "5",
            "-pix_fmt",
            "yuv420p",
            "-vf",
            "scale=512:288",
            "-c:a",
            "aac",
            "-shortest",
            output_path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        img.save(proc.stdin, "PNG")
        _, stderr = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during AFK animation creation: {stderr.decode(errors='ignore')}")

    async def create_afk_animation(self, text_lines: List[str], output_path: str):
        await self._run_in_executor(self._sync_create_afk_animation, text_lines, output_path)
        return output_path

    def _convert_to_sticker(self, video_path: str, output_path: str, fps: int = 30):
        try:
            ffprobe_cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                video_path,
            ]
            result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            duration = 3.0

        trim_duration = min(duration, 2.95)
        scale_filter = "scale='if(gt(a,1),512,-2)':'if(gt(a,1),-2,512)'"

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-t",
            str(trim_duration),
            "-vf",
            f"{scale_filter},fps={fps}",
            "-c:v",
            "libvpx-vp9",
            "-pix_fmt",
            "yuva420p",
            "-crf",
            "30",
            "-b:v",
            "0",
            "-an",
            output_path,
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during sticker conversion: {result.stderr}")

    async def video_to_sticker(self, video_path: str, output_path: str, fps: int = 30):
        await self._run_in_executor(self._convert_to_sticker, video_path, output_path, fps=fps)
        return output_path

    def _convert_video_to_gif(self, video_path: str, output_path: str):
        vf_filter = "fps=15,scale=512:-1:flags=lanczos"
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-vf",
            vf_filter,
            "-c:v",
            "gif",
            output_path,
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during GIF conversion: {result.stderr}")

    async def video_to_gif(self, video_path: str, output_path: str):
        await self._run_in_executor(self._convert_video_to_gif, video_path, output_path)
        return output_path

    def _add_text_to_video(self, video_path: str, output_path: str, top_text: str, bottom_text: str):
        font = self._get_font(70)

        def escape_ffmpeg_text(text):
            return text.replace("'", "'\\''")

        top_drawtext = (
            f"drawtext=fontfile='{font.path}':text='{escape_ffmpeg_text(top_text.upper())}':"
            "fontcolor=white:fontsize=80:borderw=2:bordercolor=black:"
            "x=(w-text_w)/2:y=20"
        )
        bottom_drawtext = (
            f"drawtext=fontfile='{font.path}':text='{escape_ffmpeg_text(bottom_text.upper())}':"
            "fontcolor=white:fontsize=80:borderw=2:bordercolor=black:"
            "x=(w-text_w)/2:y=h-text_h-20"
        )

        filters_list = []
        if top_text:
            filters_list.append(top_drawtext)
        if bottom_text:
            filters_list.append(bottom_drawtext)

        vf_filter = ",".join(filters_list)

        ffmpeg_cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", vf_filter, "-c:a", "copy", output_path]

        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during animated meme creation: {result.stderr}")

    async def add_text_to_video(self, video_path: str, output_path: str, top_text: str = "", bottom_text: str = ""):
        await self._run_in_executor(self._add_text_to_video, video_path, output_path, top_text, bottom_text)
        return output_path

    def _sync_video_to_audio(self, video_path: str, output_path: str):
        ffmpeg_cmd = ["ffmpeg", "-y", "-i", video_path, "-q:a", "0", "-map", "a", output_path]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during audio extraction: {result.stderr}")

    async def video_to_audio(self, video_path: str, output_path: str):
        await self._run_in_executor(self._sync_video_to_audio, video_path, output_path)
        return output_path

    def _sync_trim_video(self, video_path: str, output_path: str, start_time: str, end_time: str):
        ffmpeg_cmd = ["ffmpeg", "-y", "-i", video_path, "-ss", start_time, "-to", end_time, "-c", "copy", output_path]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during video trim: {result.stderr}")

    async def trim_video(self, video_path: str, output_path: str, start_time: str, end_time: str):
        await self._run_in_executor(self._sync_trim_video, video_path, output_path, start_time, end_time)
        return output_path

    def _sync_change_speed(self, video_path: str, output_path: str, speed_factor: float):
        if speed_factor <= 0:
            raise ValueError("Speed factor must be positive.")

        filter_complex = f"[0:v]setpts={1/speed_factor}*PTS[v];[0:a]atempo={speed_factor}[a]"

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "[a]",
            output_path,
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during speed change: {result.stderr}")

    async def change_speed(self, video_path: str, output_path: str, speed_factor: float):
        await self._run_in_executor(self._sync_change_speed, video_path, output_path, speed_factor)
        return output_path
