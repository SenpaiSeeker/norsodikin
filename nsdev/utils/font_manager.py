import os
import random
import glob
from typing import List
from importlib import resources

from PIL import Image, ImageDraw, ImageFont


class FontManager:
    def __init__(self):
        try:
            self.fonts_dir = resources.files('assets').joinpath('fonts')
            self.available_fonts: List[str] = [str(f) for f in self.fonts_dir.iterdir()]

        except (ModuleNotFoundError, FileNotFoundError):
            self.fonts_dir_ref = None
            self.available_fonts = []

    def _get_default_pfp(self, initial: str) -> bytes:
        from io import BytesIO
        
        W, H = (256, 256)
        
        hue = random.uniform(0, 360)
        
        from colorsys import hsv_to_rgb
        r, g, b = [int(c * 255) for c in hsv_to_rgb(hue / 360, 0.6, 0.85)]
        bg_color = (r, g, b)

        img = Image.new('RGBA', (W, H), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        draw.ellipse([(0, 0), (W, H)], fill=bg_color)
        
        try:
            with resources.as_file(self.fonts_dir_ref.joinpath("NotoSans-Bold.ttf")) as font_path:
                font = ImageFont.truetype(str(font_path), 150)
        except (IOError, FileNotFoundError, AttributeError):
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), initial, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        position = ((W - text_w) / 2, (H - text_h) / 2 - 15)
        draw.text(position, initial, font=font, fill=(255, 255, 255))
        
        output = BytesIO()
        img.save(output, format='PNG')
        return output.getvalue()

    def _get_font(self, font_size: int):
        if self.available_fonts:
            try:
                random_path = random.choice([os.path.basename(p) for p in self.available_fonts])
                random_font_ref = self.fonts_dir_ref.joinpath(random_path)
                with resources.as_file(random_font_ref) as font_path:
                    return ImageFont.truetype(str(font_path), font_size)
            except (IOError, IndexError, FileNotFoundError):
                pass
        
        try:
            with resources.as_file(self.fonts_dir_ref.joinpath("NotoSans-Regular.ttf")) as font_path:
                return ImageFont.truetype(str(font_path), font_size)
        except (IOError, FileNotFoundError, AttributeError):
            return ImageFont.load_default()
