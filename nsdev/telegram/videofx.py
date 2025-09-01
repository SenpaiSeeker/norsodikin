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
        mode = "RGB"
        dummy_img = Image.new(mode, (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        text_widths = [dummy_draw.textbbox((0, 0), line, font=font)[2] for line in text_lines]
        text_heights = [dummy_draw.textbbox((0, 0), line, font=font)[3] for line in text_lines]
        
        base_w = max(max(text_widths) + 40, 512)
        canvas_w = base_w - (base_w % 2)
        
        total_h = sum(text_heights) + (len(text_lines) * 20)
        base_h = max(total_h, 512)
        canvas_h = base_h - (base_h % 2)
        
        if blink and blink_rate > 0:
            period = 1.0 / blink_rate
            on_duration = max(0.0, min(1.0, blink_duty)) * period
        else:
            period = None
            on_duration = None

        def make_frame(t):
            base = Image.new(mode, (canvas_w, canvas_h), (255, 255, 255, 0))
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
                    
            rr = int(r * intensity)
            gg = int(g * intensity)
            bb = int(b * intensity)
            current_y = (canvas_h - total_h) / 2

            for i, line in enumerate(text_lines):
                line_w, line_h = dummy_draw.textbbox((0, 0), line, font=font)[2:4]
                position = ((canvas_w - line_w) / 2, current_y)
                draw_base.text(position, line, font=font, fill=(rr, gg, bb))
                current_y += line_h + 20
                
            arr = np.array(base, dtype=np.uint8)
            return arr

        animation = VideoClip(make_frame, duration=duration)
        animation.write_videofile(
            output_path, fps=fps, codec="libx264", logger=None, ffmpeg_params=["-pix_fmt", "yuv420p"]
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
        )
        return output_path

    def _convert_to_sticker(self, video_path: str, output_path: str, fps: int = 30):
        clip = VideoFileClip(video_path)
        max_duration = min(clip.duration, 2.95)
        trimmed_clip = clip.subclipped(0, max_duration)
        
        if trimmed_clip.w >= trimmed_clip.h:
            resized_clip = trimmed_clip.resized(width=512)
        else:
            resized_clip = trimmed_clip.resized(height=512)
        
        final_clip = resized_clip.with_fps(fps).with_position(("center", "center"))
        ffmpeg_params = ["-pix_fmt", "yuv420p", "-crf", "30", "-b:v", "0"]
        
        final_clip.write_videofile(
            output_path, codec="libvpx-vp9", audio=False, logger=None, ffmpeg_params=ffmpeg_params
        )
        
        clip.close()
        trimmed_clip.close()
        resized_clip.close()
        final_clip.close()

    async def video_to_sticker(self, video_path: str, output_path: str, fps: int = 30):
        await self._run_in_executor(self._convert_to_sticker, video_path, output_path, fps=fps)
        return output_path
