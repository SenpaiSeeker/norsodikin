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

    def _sync_add_watermark(
        self,
        image_bytes: bytes,
        text: str,
        position: Tuple[int, int] = (10, 10),
        font_size: int = 30,
        opacity: int = 128,
    ) -> bytes:
        img = Image.open(BytesIO(image_bytes)).convert("RGBA")
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        font = self._get_font(font_size)
        draw = ImageDraw.Draw(txt_layer)
        draw.text(position, text, font=font, fill=(255, 255, 255, opacity))
        watermarked_img = Image.alpha_composite(img, txt_layer)
        output_buffer = BytesIO()
        watermarked_img.save(output_buffer, format="PNG")
        return output_buffer.getvalue()

    async def add_watermark(
        self,
        image_bytes: bytes,
        text: str,
        position: Tuple[int, int] = (10, 10),
        font_size: int = 30,
        opacity: int = 128,
    ) -> bytes:
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

        def get_font_from_package(font_filename, size):
            font_resource = resources.files('assets').joinpath('fonts', font_filename)
            with resources.as_file(font_resource) as font_path:
                return ImageFont.truetype(str(font_path), size)

        def has_glyph(font, char):
            try:
                return font.getmask(char).getbbox()
            except AttributeError:
                return False

        font_name = get_font_from_package("NotoSans-Regular.ttf", 40)
        font_quote = get_font_from_package("NotoSans-Regular.ttf", 50)
        emoji_font = get_font_from_package("NotoColorEmoji-Regular.ttf", 50)

        def segment_text(text, main_font, fallback_font):
            segments = []
            current_segment_text = ""
            current_segment_font = None

            for char in text:
                font_for_char = main_font if has_glyph(main_font, char) else fallback_font
                
                if current_segment_font and font_for_char != current_segment_font:
                    segments.append((current_segment_text, current_segment_font))
                    current_segment_text = ""

                current_segment_text += char
                current_segment_font = font_for_char
            
            if current_segment_text:
                segments.append((current_segment_text, current_segment_font))
            
            return segments

        def draw_segmented_text(draw, pos, segments, fill_color):
            x, y = pos
            for segment_text, font in segments:
                if font == fallback_font:
                    draw.text((x, y), segment_text, font=font, embedded_color=True)
                else:
                    draw.text((x, y), segment_text, font=font, fill=fill_color)
                x += font.getlength(segment_text)

        def get_segmented_text_width(segments):
            width = 0
            for segment_text, font in segments:
                width += font.getlength(segment_text)
            return width

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

        bg_color, text_color, name_color = ("#161616", "#FFFFFF", "#AAAAAA") if not invert else ("#FFFFFF", "#161616", "#555555")

        TEXT_LEFT_MARGIN = 200
        RIGHT_MARGIN = 80
        MAX_IMAGE_WIDTH = 1280
        MIN_IMAGE_WIDTH = 512
        MAX_TEXT_WIDTH = MAX_IMAGE_WIDTH - TEXT_LEFT_MARGIN - RIGHT_MARGIN

        final_lines_segmented = []
        initial_lines = text.splitlines()
        if not initial_lines:
            initial_lines = [" "]

        for line in initial_lines:
            if not line.strip():
                final_lines_segmented.append([(" ", font_quote)])
                continue
            
            words = line.split(' ')
            current_line_segments = []
            for word in words:
                word_segments = segment_text(word + ' ', font_quote, emoji_font)
                
                temp_width = get_segmented_text_width(current_line_segments + word_segments)
                
                if temp_width > MAX_TEXT_WIDTH and current_line_segments:
                    final_lines_segmented.append(current_line_segments)
                    current_line_segments = segment_text(word + ' ', font_quote, emoji_font)
                else:
                    current_line_segments.extend(word_segments)
            
            final_lines_segmented.append(current_line_segments)

        longest_line_width = 0
        for segments in final_lines_segmented:
            line_width = get_segmented_text_width(segments)
            if line_width > longest_line_width:
                longest_line_width = line_width
                
        name_segments = segment_text(user_name, font_name, emoji_font)
        name_width = get_segmented_text_width(name_segments)
        longest_line_width = max(longest_line_width, name_width)

        image_w = int(TEXT_LEFT_MARGIN + longest_line_width + RIGHT_MARGIN)
        image_w = max(MIN_IMAGE_WIDTH, image_w)
        image_w = min(MAX_IMAGE_WIDTH, image_w)
        
        line_height = font_quote.getbbox("Tg")[3] + 10
        name_height = font_name.getbbox("Tg")[3]
        
        quote_h = len(final_lines_segmented) * line_height
        
        image_h = max(200, quote_h + name_height + 100)
        
        img = Image.new("RGB", (image_w, image_h), bg_color)
        draw = ImageDraw.Draw(img)

        img.paste(pfp, (50, 40), pfp)

        current_h = (image_h - (quote_h + name_height + 10)) / 2
        draw_segmented_text(draw, (TEXT_LEFT_MARGIN, current_h), name_segments, name_color)
        current_h += name_height + 10

        for segments in final_lines_segmented:
            draw_segmented_text(draw, (TEXT_LEFT_MARGIN, current_h), segments, text_color)
            current_h += line_height

        output = BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()
    
    async def create_quote(self, text: str, user_name: str, pfp_bytes: bytes, invert: bool = False) -> bytes:
        return await self._run_in_executor(self._sync_create_quote, text, user_name, pfp_bytes, invert)
