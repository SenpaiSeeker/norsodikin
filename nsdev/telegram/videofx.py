import asyncio
import functools
import math
import os
from typing import List

import numpy as np
from moviepy import VideoClip, VideoFileClip
from PIL import Image, ImageDraw

from ..utils.font_manager import FontManager


class VideoFX(FontManager):
    def __init__(self):
        super().__init__()

    async def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        call = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, call)

    def _measure_text(self, draw: ImageDraw.ImageDraw, text: str, font) -> (int, int):
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            if w > 0 and h > 0:
                return int(w), int(h)
        except Exception:
            pass

        try:
            w, h = draw.textsize(text, font=font)
            if w > 0 and h > 0:
                return int(w), int(h)
        except Exception:
            pass

        try:
            mask = font.getmask(text)
            return int(mask.size[0]), int(mask.size[1])
        except Exception:
            avg_char_w = max(6, int(font.size * 0.6)) if hasattr(font, "size") else 8
            w = avg_char_w * max(1, len(text))
            h = getattr(font, "size", 16) + 4
            return int(w), int(h)

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
        transparent: bool = True,
    ):
        text_lines = [t.strip() for t in text_lines if t and t.strip()]
        if not text_lines:
            text_lines = [" "]

        font = self._get_font(font_size)

        mode = "RGBA" if transparent else "RGB"
        dummy_bg = (0, 0, 0, 0) if mode == "RGBA" else (0, 0, 0)
        dummy_img = Image.new(mode, (10, 10), dummy_bg)
        dummy_draw = ImageDraw.Draw(dummy_img)

        text_metrics = [self._measure_text(dummy_draw, line, font) for line in text_lines]
        text_widths = [w for w, h in text_metrics]
        text_heights = [h for w, h in text_metrics]

        base_w = max(max(text_widths) + 40, 512)
        canvas_w = int(base_w - (base_w % 2))

        total_h = sum(text_heights) + (len(text_lines) * 20)
        base_h = max(total_h, 512)
        canvas_h = int(base_h - (base_h % 2))

        if blink and blink_rate > 0:
            period = 1.0 / blink_rate
            on_duration = max(0.0, min(1.0, blink_duty)) * period
        else:
            period = None
            on_duration = None

        def make_frame(t):
            bg_color = (0, 0, 0, 0) if mode == "RGBA" else (0, 0, 0)
            base = Image.new(mode, (canvas_w, canvas_h), bg_color)
            draw_base = ImageDraw.Draw(base)

            r = int(127 * (1 + math.sin(t * 5 + 0))) + 64
            g = int(127 * (1 + math.sin(t * 5 + 2))) + 64
            b = int(127 * (1 + math.sin(t * 5 + 4))) + 64

            intensity = 1.0
            if blink and period is not None:
                if blink_smooth:
                    intensity = 0.5 * (1 + math.sin(2 * math.pi * blink_rate * t - math.pi / 2))
                    intensity = max(0.0, min(1.0, intensity))
                else:
                    phase = t % period
                    intensity = 1.0 if phase < on_duration else 0.0

            alpha_byte = int(255 * intensity) if mode == "RGBA" else 255
            rr, gg, bb = rr_val, gg_val, bb_val = r, g, b

            current_y = (canvas_h - total_h) / 2
            for i, line in enumerate(text_lines):
                line_w = text_widths[i]
                line_h = text_heights[i]
                pos = ((canvas_w - line_w) / 2, current_y)
                if mode == "RGBA":
                    fill = (rr, gg, bb, alpha_byte)
                else:
                    fill = (rr, gg, bb)
                draw_base.text(pos, line, font=font, fill=fill)
                current_y += line_h + 20

            arr = np.array(base, dtype=np.uint8)
            return arr

        animation = VideoClip(make_frame, duration=duration)

        if transparent:
            ffmpeg_params = ["-pix_fmt", "yuva420p", "-crf", "30", "-b:v", "0"]
            codec = "libvpx-vp9"
        else:
            ffmpeg_params = ["-pix_fmt", "yuv420p"]
            codec = "libx264"

        animation.write_videofile(
            output_path, fps=fps, codec=codec, logger=None, ffmpeg_params=ffmpeg_params
        )
        animation.close()

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
        transparent: bool = True,
    ):
        text_lines = text.split(";") if ";" in text else text.splitlines()
        await self._run_in_executor(
            self._create_rgb_video,
            text_lines,
            output_path,
            duration,
            fps,
            blink=blink,
            blink_rate=blink_rate,
            blink_duty=blink_duty,
            blink_smooth=blink_smooth,
            font_size=font_size,
            transparent=transparent,
        )
        return output_path

    def _convert_to_sticker(self, video_path: str, output_path: str, fps: int = 30, preserve_alpha: bool = True):
        clip = VideoFileClip(video_path)
        max_duration = min(clip.duration, 2.95)
        trimmed_clip = clip.subclipped(0, max_duration)

        if trimmed_clip.w >= trimmed_clip.h:
            resized_clip = trimmed_clip.resized(width=512)
        else:
            resized_clip = trimmed_clip.resized(height=512)

        final_clip = resized_clip.with_fps(fps).with_position(("center", "center"))

        if preserve_alpha:
            ffmpeg_params = ["-pix_fmt", "yuva420p", "-crf", "30", "-b:v", "0"]
        else:
            ffmpeg_params = ["-pix_fmt", "yuv420p", "-crf", "30", "-b:v", "0"]

        final_clip.write_videofile(
            output_path, codec="libvpx-vp9", audio=False, logger=None, ffmpeg_params=ffmpeg_params
        )
        clip.close()
        trimmed_clip.close()
        resized_clip.close()
        final_clip.close()
        
        
    async def video_to_sticker(self, video_path: str, output_path: str, fps: int = 30, preserve_alpha: bool = True):
        await self._run_in_executor(self._convert_to_sticker, video_path, output_path, fps, preserve_alpha)
        return output_path
