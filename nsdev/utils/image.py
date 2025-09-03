import asyncio
from functools import partial
from io import BytesIO
from typing import Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from .font_manager import FontManager


class ImageManipulator(FontManager):
    def __init__(self):
        super().__init__()

    def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, partial(func, *args, **kwargs))

    def _sync_add_watermark(
        self, image_bytes: bytes, text: str, position: Tuple[int, int] = (10, 10), font_size: int = 30, opacity: int = 128
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
        self, image_bytes: bytes, text: str, position: Tuple[int, int] = (10, 10), font_size: int = 30, opacity: int = 128
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
            outline_color = "black"
            text_color = "white"
            for offset in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                draw.text((x + offset[0], y + offset[1]), text, font=font, fill=outline_color)
            draw.text((x, y), text, font=font, fill=text_color)

        top_text = top_text.upper()
        bottom_text = bottom_text.upper()

        if top_text:
            bbox = draw.textbbox((0, 0), top_text, font=font)
            top_w, top_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
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
            sepia_palette = []
            for i in range(256):
                r = int(min(255, i * 1.2))
                g = int(min(255, i * 1.0))
                b = int(min(255, i * 0.8))
                sepia_palette.extend((r, g, b))
            grayscale_img.putpalette(sepia_palette)
            processed_img = grayscale_img.convert("RGB")
        elif filter_name == "invert":
            processed_img = ImageOps.invert(img)
        elif filter_name == "blur":
            processed_img = img.filter(ImageFilter.GaussianBlur(radius=5))
        elif filter_name == "sharpen":
            processed_img = img.filter(ImageFilter.SHARPEN)
        else:
            raise ValueError(f"Filter '{filter_name}' tidak dikenal.")

        output_buffer = BytesIO()
        processed_img.save(output_buffer, format="JPEG")
        return output_buffer.getvalue()

    async def apply_filter(self, image_bytes: bytes, filter_name: str) -> bytes:
        return await self._run_in_executor(self._sync_apply_filter, image_bytes, filter_name)
