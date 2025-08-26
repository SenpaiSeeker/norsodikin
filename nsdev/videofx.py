import asyncio
import glob
import math
import os
import random
from typing import List

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .logger import LoggerHandler

from moviepy import VideoClip, VideoFileClip


class VideoFX:
    def __init__(self, fonts_dir: str = "fonts"):
        self.log = LoggerHandler()
        self.fonts_dir = fonts_dir
        self.available_fonts: List[str] = []
        if os.path.isdir(self.fonts_dir):
            ttf = glob.glob(os.path.join(self.fonts_dir, "*.ttf"))
            otf = glob.glob(os.path.join(self.fonts_dir, "*.otf"))
            self.available_fonts = ttf + otf

        if not self.available_fonts:
            self.log.print(
                f"{self.log.YELLOW}Peringatan: tidak ada font di '{self.fonts_dir}'. Menggunakan font default."
            )

    def _get_font(self, font_size: int):
        if self.available_fonts:
            path = random.choice(self.available_fonts)
            try:
                return ImageFont.truetype(path, font_size)
            except IOError:
                self.log.print(f"{self.log.YELLOW}Gagal memuat font '{path}'. Menggunakan default.")
                return ImageFont.load_default()
        return ImageFont.load_default()

    async def _run_in_executor(self, func, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func, *args)

    def _create_rgb_video(self, text_lines: List[str], output_path: str, duration: float, fps: int):
        text_lines = [t.strip() for t in text_lines if t and t.strip()]
        if not text_lines:
            text_lines = [" "]

        font_size = 90
        font = self._get_font(font_size)

        dummy = Image.new("RGB", (1,1))
        draw_dummy = ImageDraw.Draw(dummy)
        widths = [draw_dummy.textbbox((0,0), line, font=font)[2] for line in text_lines]
        heights = [draw_dummy.textbbox((0,0), line, font=font)[3] for line in text_lines]

        canvas_w = max(max(widths) + 40, 512)
        total_h = sum(heights) + len(text_lines)*20
        canvas_h = max(total_h, 512)

        def make_frame(t):
            img = Image.new("RGB", (canvas_w, canvas_h), "black")
            draw = ImageDraw.Draw(img)
            r = int(127*(1 + math.sin(t*15 + 0))) + 128
            g = int(127*(1 + math.sin(t*15 + 2))) + 128
            b = int(127*(1 + math.sin(t*15 + 4))) + 128

            y = (canvas_h - total_h) / 2
            for i, line in enumerate(text_lines):
                w = widths[i]
                h = heights[i]
                pos = ((canvas_w - w)/2, y)
                draw.text(pos, line, font=font, fill=(r,g,b))
                y += h + 20

            return np.array(img)

        animation = VideoClip(make_frame, duration=duration)
        animation.write_videofile(output_path, fps=fps, codec="libx264", logger=None)
        animation.close()

    async def text_to_video(self, text: str, output_path: str, duration: float = 3.0, fps: int = 24):
        lines = text.split(";") if ";" in text else text.splitlines()
        await self._run_in_executor(self._create_rgb_video, lines, output_path, duration, fps)
        return output_path

    def _convert_to_sticker(self, video_path: str, output_path: str):
        clip = VideoFileClip(video_path)

        duration = min(clip.duration, 2.95)
        trimmed = clip.subclipped(0, duration)

        if trimmed.w >= trimmed.h:
            resized = trimmed.with_resized(width=512)
        else:
            resized = trimmed.with_resized(height=512)

        final = resized.with_position(("center", "center"))

        final.write_videofile(output_path, codec="libvpx-vp9", audio=False, logger=None)

        clip.close()
        trimmed.close()
        resized.close()
        final.close()

    async def video_to_sticker(self, video_path: str, output_path: str):
        await self._run_in_executor(self._convert_to_sticker, video_path, output_path)
        return output_path
