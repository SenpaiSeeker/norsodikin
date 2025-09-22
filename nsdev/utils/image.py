import asyncio
from functools import partial
from io import BytesIO
from typing import Tuple
import os
from importlib import resources

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps, ImageFont

from .font_manager import FontManager

try:
    from rembg import remove as remove_bg
except ImportError:
    remove_bg = None


class ImageManipulator(FontManager):
    def __init__(self):
        super().__init__()

    def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, partial(func, *args, **kwargs))
    
    def _sync_add_watermark(self, image_bytes: bytes, text: str, position: Tuple[int, int] = (10, 10), font_size: int = 30, opacity: int = 128) -> bytes:
        img = Image.open(BytesIO(image_bytes)).convert("RGBA")
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        font = self._get_font(font_size)
        draw = ImageDraw.Draw(txt_layer)
        draw.text(position, text, font=font, fill=(255, 255, 255, opacity))
        watermarked_img = Image.alpha_composite(img, txt_layer)
        output_buffer = BytesIO()
        watermarked_img.save(output_buffer, format="PNG")
        return output_buffer.getvalue()

    async def add_watermark(self, image_bytes: bytes, text: str, position: Tuple[int, int] = (10, 10), font_size: int = 30, opacity: int = 128) -> bytes:
        return await self._run_in_executor(self._sync_add_watermark, image_bytes, text, position, font_size, opacity)

    def _sync_resize(self, image_bytes: bytes, size: Tuple[int, int], keep_aspect_ratio: bool = True) -> bytes:
        img = Image.open(BytesIO(image_bytes))
        if keep_aspect_ratio:
            img.thumbnail(size, Image.LANCZOS)
        else:
            img = img.resize(size, Image.LANCZOS)
        output_buffer = BytesIO()
        output_format = img.format if img.format in ["JPEG", "PNG", "WEBP"] else "PNG"
        img.save(output_buffer, format=output_format)
        return output_buffer.getvalue()

    async def resize(self, image_bytes: bytes, size: Tuple[int, int], keep_aspect_ratio: bool = True) -> bytes:
        return await self._run_in_executor(self._sync_resize, image_bytes, size, keep_aspect_ratio)

    def _sync_convert_format(self, image_bytes: bytes, output_format: str = "PNG") -> bytes:
        img = Image.open(BytesIO(image_bytes))
        if img.mode == "RGBA" and output_format.upper() == "JPEG":
            img = img.convert("RGB")
        output_buffer = BytesIO()
        img.save(output_buffer, format=output_format.upper())
        return output_buffer.getvalue()

    async def convert_format(self, image_bytes: bytes, output_format: str = "PNG") -> bytes:
        return await self._run_in_executor(self._sync_convert_format, image_bytes, output_format)

    def _sync_create_meme(self, image_bytes: bytes, top_text: str, bottom_text: str) -> bytes:
        img = Image.open(BytesIO(image_bytes)).convert("RGBA")
        draw = ImageDraw.Draw(img)
        font_size = int(img.width / 10)
        font = self._get_font(font_size)

        def draw_text_with_outline(text, x, y):
            outline_color, text_color = "black", "white"
            for offset in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                draw.text((x + offset[0], y + offset[1]), text, font=font, fill=outline_color)
            draw.text((x, y), text, font=font, fill=text_color)

        top_text, bottom_text = top_text.upper(), bottom_text.upper()

        if top_text:
            bbox = draw.textbbox((0, 0), top_text, font=font)
            top_w = bbox[2] - bbox[0]
            draw_text_with_outline(top_text, (img.width - top_w) / 2, 10)
        if bottom_text:
            bbox = draw.textbbox((0, 0), bottom_text, font=font)
            bottom_w, bottom_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw_text_with_outline(bottom_text, (img.width - bottom_w) / 2, img.height - bottom_h - 15)

        output_buffer = BytesIO()
        img.save(output_buffer, format="PNG")
        return output_buffer.getvalue()

    async def create_meme(self, image_bytes: bytes, top_text: str, bottom_text: str) -> bytes:
        return await self._run_in_executor(self._sync_create_meme, image_bytes, top_text, bottom_text)

    def _sync_apply_filter(self, image_bytes: bytes, filter_name: str) -> bytes:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        if filter_name == "grayscale":
            processed_img = ImageOps.grayscale(img)
        elif filter_name == "sepia":
            grayscale_img = ImageOps.grayscale(img)
            sepia_palette = [ component for i in range(256) for component in (int(min(255, i * 1.2)), int(min(255, i * 1.0)), int(min(255, i * 0.8))) ]
            grayscale_img.putpalette(sepia_palette)
            processed_img = grayscale_img.convert("RGB")
        elif filter_name == "invert":
            processed_img = ImageOps.invert(img)
        elif filter_name == "blur":
            processed_img = img.filter(ImageFilter.GaussianBlur(radius=5))
        elif filter_name == "sharpen":
            processed_img = img.filter(ImageFilter.SHARPEN)
        elif filter_name == "hell":
            enhancer = ImageEnhance.Contrast(img)
            img_contrasted = enhancer.enhance(1.5)
            img_gray = ImageOps.grayscale(img_contrasted)
            processed_img = ImageOps.colorize(img_gray, black=(20, 0, 0), mid=(200, 50, 0), white=(255, 220, 50))
        else:
            raise ValueError(f"Filter '{filter_name}' tidak dikenal.")
        output_buffer = BytesIO()
        processed_img.save(output_buffer, format="JPEG")
        return output_buffer.getvalue()

    async def apply_filter(self, image_bytes: bytes, filter_name: str) -> bytes:
        return await self._run_in_executor(self._sync_apply_filter, image_bytes, filter_name)

    def _sync_remove_background(self, image_bytes: bytes) -> bytes:
        if not remove_bg:
            raise ImportError("Pustaka 'rembg' tidak terinstal. Silakan instal dengan `pip install norsodikin[ai]`")
        return remove_bg(image_bytes)

    async def remove_background(self, image_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._sync_remove_background, image_bytes)

    def _sync_convert_sticker_to_png(self, sticker_bytes: bytes) -> bytes:
        img = Image.open(BytesIO(sticker_bytes))
        output_buffer = BytesIO()
        img.save(output_buffer, format="PNG")
        return output_buffer.getvalue()

    async def convert_sticker_to_png(self, sticker_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._sync_convert_sticker_to_png, sticker_bytes)

    def _sync_create_quote(self, text: str, user_name: str, pfp_bytes: bytes, invert: bool) -> bytes:
        pfp_data = pfp_bytes
        if not pfp_data:
            initial = user_name[0].upper()
            pfp_data = self._get_default_pfp(initial)

        pfp = Image.open(BytesIO(pfp_data)).convert("RGBA")
        pfp = pfp.resize((120, 120))
        
        mask = Image.new('L', pfp.size, 0)
        draw_mask = ImageDraw.Draw(mask) 
        draw_mask.ellipse((0, 0) + pfp.size, fill=255)
        pfp.putalpha(mask)
        
        def get_font_path_str(filename):
             with resources.as_file(resources.files('assets').joinpath('fonts', filename)) as font_path:
                return str(font_path)

        font_paths = [
            get_font_path_str("NotoSans-Regular.ttf"),
            get_font_path_str("NotoColorEmoji-Regular.ttf"),
            get_font_path_str("NotoSansSymbols2-Regular.ttf")
        ]

        font_name = ImageFont.truetype(font_paths[0], 40, layout_engine=ImageFont.Layout.RAQM)
        font_quote = ImageFont.truetype(font_paths[0], 50, layout_engine=ImageFont.Layout.RAQM)

        def get_text_width(font, text, features):
            try:
                return font.getbbox(text, features=["-liga"], font_features=features)[2]
            except TypeError:
                return font.getlength(text)


        bg_color, text_color, name_color = ("#161616", "#FFFFFF", "#AAAAAA") if not invert else ("#FFFFFF", "#161616", "#555555")

        TEXT_LEFT_MARGIN, RIGHT_MARGIN, MAX_WIDTH, MIN_WIDTH = 200, 80, 1280, 512
        MAX_TEXT_WIDTH = MAX_WIDTH - TEXT_LEFT_MARGIN - RIGHT_MARGIN
        
        final_lines = []
        for line in text.splitlines():
            words = (line if line.strip() else " ").split(' ')
            current_line = ""
            for word in words:
                test_line = (current_line + " " + word).strip()
                if get_text_width(font_quote, test_line, font_paths) > MAX_TEXT_WIDTH:
                    final_lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            final_lines.append(current_line)
        
        longest_line_width = 0
        for line in final_lines:
            line_width = get_text_width(font_quote, line, font_paths)
            if line_width > longest_line_width:
                longest_line_width = line_width
        
        name_width = get_text_width(font_name, user_name, font_paths)
        longest_line_width = max(longest_line_width, name_width)
        
        image_w = min(MAX_WIDTH, max(MIN_WIDTH, int(TEXT_LEFT_MARGIN + longest_line_width + RIGHT_MARGIN)))

        quote_h = sum([font_quote.getbbox(l)[3] - font_quote.getbbox(l)[1] for l in final_lines]) + (len(final_lines) - 1) * 15
        name_h = font_name.getbbox(user_name)[3] - font_name.getbbox(user_name)[1]
        
        image_h = max(200, quote_h + name_h + 120)
        
        img = Image.new("RGB", (image_w, image_h), bg_color)
        draw = ImageDraw.Draw(img)
        img.paste(pfp, (50, 60), pfp)

        current_h = (image_h - (quote_h + name_h + 20)) / 2
        
        draw.text((TEXT_LEFT_MARGIN, current_h), user_name, font=font_name, fill=name_color, features=["-liga"], font_features=font_paths)
        current_h += name_h + 20

        for line in final_lines:
            draw.text((TEXT_LEFT_MARGIN, current_h), line, font=font_quote, fill=text_color, features=["-liga"], font_features=font_paths)
            current_h += (font_quote.getbbox(line)[3] - font_quote.getbbox(line)[1]) + 15
            
        output = BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()

    async def create_quote(self, text: str, user_name: str, pfp_bytes: bytes, invert: bool = False) -> bytes:
        return await self._run_in_executor(self._sync_create_quote, text, user_name, pfp_bytes, invert)
