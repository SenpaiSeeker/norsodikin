import asyncio
import glob
import math
import os
import random

import numpy as np
from moviepy import VideoClip, VideoFileClip
from PIL import Image, ImageDraw, ImageFont

from .logger import LoggerHandler


class VideoFX:
    def __init__(self, fonts_dir: str = "fonts"):
        self.log = LoggerHandler()
        self.fonts_dir = fonts_dir
        self.available_fonts = []
        if os.path.isdir(self.fonts_dir):
            ttf_files = glob.glob(os.path.join(self.fonts_dir, "*.ttf"))
            otf_files = glob.glob(os.path.join(self.fonts_dir, "*.otf"))
            self.available_fonts = ttf_files + otf_files

        if not self.available_fonts:
            self.log.print(
                f"{self.log.YELLOW}Peringatan: Tidak ada font ditemukan di folder 'fonts'. Akan menggunakan font default."
            )

    def _get_font(self, font_size: int):
        if self.available_fonts:
            random_font_path = random.choice(self.available_fonts)
            try:
                return ImageFont.truetype(random_font_path, font_size)
            except OSError:
                self.log.print(
                    f"{self.log.YELLOW}Peringatan: Gagal memuat font '{random_font_path}'. Menggunakan font default."
                )
                return ImageFont.load_default()
        return ImageFont.load_default()

    async def _run_in_executor(self, func, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func, *args)

    def _create_rgb_video(self, text_lines: list, output_path: str, duration: float, fps: int):
        font_size = 90
        font = self._get_font(font_size)

        dummy_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        text_widths = [dummy_draw.textbbox((0, 0), line, font=font)[2] for line in text_lines]
        text_heights = [dummy_draw.textbbox((0, 0), line, font=font)[3] for line in text_lines]

        canvas_w = max(max(text_widths) + 40, 512)
        total_h = sum(text_heights) + (len(text_lines) * 20)
        canvas_h = max(total_h, 512)

        def make_frame(t):
            img = Image.new("RGB", (canvas_w, canvas_h), "black")
            draw = ImageDraw.Draw(img)

            r = int(127 * (1 + math.sin(t * 15 + 0))) + 128
            g = int(127 * (1 + math.sin(t * 15 + 2))) + 128
            b = int(127 * (1 + math.sin(t * 15 + 4))) + 128

            current_y = (canvas_h - total_h) / 2
            for i, line in enumerate(text_lines):
                line_w = text_widths[i]
                line_h = text_heights[i]
                position = ((canvas_w - line_w) / 2, current_y)
                draw.text(position, line, font=font, fill=(r, g, b))
                current_y += line_h + 20

            return np.array(img)

        animation = VideoClip(make_frame, duration=duration)
        animation.write_videofile(output_path, fps=fps, codec="libx264", logger=None)
        animation.close()

    async def text_to_video(self, text: str, output_path: str, duration: float = 3.0, fps: int = 24):
        text_lines = text.split(";")
        await self._run_in_executor(self._create_rgb_video, text_lines, output_path, duration, fps)
        return output_path

    def _convert_to_sticker(self, video_path: str, output_path: str):
        clip = VideoFileClip(video_path)

        max_duration = min(clip.duration, 2.95)
        trimmed_clip = clip.subclipped(0, max_duration)

        if trimmed_clip.w >= trimmed_clip.h:
            resized_clip = trimmed_clip.resized(width=512)
        else:
            resized_clip = trimmed_clip.resized(height=512)

        final_clip = resized_clip.with_position(("center", "center"))
        final_clip.write_videofile(output_path, codec="libvpx-vp9", audio=False, logger=None)

        clip.close()
        trimmed_clip.close()
        resized_clip.close()
        final_clip.close()

    async def video_to_sticker(self, video_path: str, output_path: str):
        await self._run_in_executor(self._convert_to_sticker, video_path, output_path)
        return output_path
