import os
import random
import glob
from typing import List
from importlib import resources

from PIL import Image, ImageDraw, ImageFont


class FontManager:
    def __init__(self):
        self.fonts_dir = resources.files('nsdev').joinpath('assets', 'fonts')
        self.available_fonts: List[str] = [str(f) for f in self.fonts_dir.iterdir()]

    def _get_default_pfp(self, initial: str) -> bytes:
        from io import BytesIO
        
        W, H = (200, 200)
        bg_color = (120, 120, 120)
        img = Image.new('RGB', (W, H), color=bg_color)
        
        font = self._get_font(100)
        draw = ImageDraw.Draw(img)
        
        bbox = draw.textbbox((0, 0), initial, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        position = ((W-text_w)/2, (H-text_h)/2 - 10)
        draw.text(position, initial, font=font, fill=(255, 255, 255))
        
        output = BytesIO()
        img.save(output, format='PNG')
        return output.getvalue()

    def _get_font(self, font_size: int):
        if self.available_fonts:
            try:
                random_font_path = random.choice(self.available_fonts)
                return ImageFont.truetype(random_font_path, font_size)
            except (IOError, IndexError):
                pass
        
        try:
            with resources.as_file(self.fonts_dir.joinpath("NotoSans-Regular.ttf")) as font_path:
                return ImageFont.truetype(str(font_path), font_size)
        except (IOError, FileNotFoundError):
            return ImageFont.load_default()
