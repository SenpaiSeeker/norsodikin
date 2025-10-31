import asyncio
import base64
import functools
import io
import math
import random
import textwrap

import httpx
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from .font_manager import FontManager


class ImageManipulator(FontManager):
    def __init__(self):
        super().__init__()
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        pfunc = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, pfunc)

    def _add_watermark_sync(self, image_bytes: bytes, text: str) -> bytes:
        with Image.open(io.BytesIO(image_bytes)).convert("RGBA") as img:
            draw = ImageDraw.Draw(img)
            try:
                font = self._get_font(size=int(img.width / 20))
            except Exception:
                font = ImageFont.load_default()

            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            x = img.width - text_width - 10
            y = img.height - text_height - 10
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 128))
            
            output = io.BytesIO()
            img.save(output, format="PNG")
            return output.getvalue()

    async def add_watermark(self, image_bytes: bytes, text: str) -> bytes:
        return await self._run_in_executor(self._add_watermark_sync, image_bytes, text)

    def _resize_sync(self, image_bytes: bytes, size: tuple) -> bytes:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = img.resize(size, Image.Resampling.LANCZOS)
            output = io.BytesIO()
            img.save(output, format="PNG")
            return output.getvalue()

    async def resize(self, image_bytes: bytes, size: tuple) -> bytes:
        return await self._run_in_executor(self._resize_sync, image_bytes, size)

    def _create_meme_sync(self, image_bytes: bytes, top_text: str, bottom_text: str) -> bytes:
        with Image.open(io.BytesIO(image_bytes)).convert("RGBA") as img:
            draw = ImageDraw.Draw(img)
            font_size = int(img.width / 10)
            try:
                font = self._get_font(size=font_size)
            except Exception:
                font = ImageFont.load_default()

            def draw_text_with_outline(text, pos, align):
                x, y = pos
                shadow_color = "black"
                text_color = "white"
                for offset in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                    draw.text((x + offset[0], y + offset[1]), text, font=font, fill=shadow_color, align=align)
                draw.text(pos, text, font=font, fill=text_color, align=align)

            if top_text:
                wrapped_top = "\n".join(textwrap.wrap(top_text.upper(), width=20))
                top_bbox = draw.textbbox((0, 0), wrapped_top, font=font, align="center")
                top_w = top_bbox[2] - top_bbox[0]
                draw_text_with_outline(wrapped_top, ((img.width - top_w) / 2, 10), "center")

            if bottom_text:
                wrapped_bottom = "\n".join(textwrap.wrap(bottom_text.upper(), width=20))
                bottom_bbox = draw.textbbox((0, 0), wrapped_bottom, font=font, align="center")
                bottom_w = bottom_bbox[2] - bottom_bbox[0]
                bottom_h = bottom_bbox[3] - bottom_bbox[1]
                draw_text_with_outline(wrapped_bottom, ((img.width - bottom_w) / 2, img.height - bottom_h - 10), "center")
            
            output = io.BytesIO()
            img.save(output, format="WEBP")
            return output.getvalue()

    async def create_meme(self, image_bytes: bytes, top_text: str, bottom_text: str) -> bytes:
        return await self._run_in_executor(self._create_meme_sync, image_bytes, top_text, bottom_text)

    def _apply_filter_sync(self, image_bytes: bytes, filter_name: str) -> bytes:
        with Image.open(io.BytesIO(image_bytes)) as img:
            if filter_name == "blur":
                img = img.filter(ImageFilter.BLUR)
            elif filter_name == "sharpen":
                img = img.filter(ImageFilter.SHARPEN)
            elif filter_name == "invert":
                img = ImageOps.invert(img.convert("RGB"))
            elif filter_name == "sepia":
                sepia = Image.new("RGB", img.size)
                pixels = sepia.load()
                for i in range(img.width):
                    for j in range(img.height):
                        r, g, b = img.getpixel((i, j))
                        tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                        tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                        tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                        pixels[i, j] = (min(255, tr), min(255, tg), min(255, tb))
                img = sepia
            elif filter_name == "hell":
                img = ImageOps.colorize(ImageOps.grayscale(img), "#000000", "#FF3333")
            else:
                raise ValueError("Filter tidak dikenal. Pilihan: blur, sharpen, invert, sepia, hell")
            
            output = io.BytesIO()
            img.save(output, format="JPEG")
            return output.getvalue()

    async def apply_filter(self, image_bytes: bytes, filter_name: str) -> bytes:
        return await self._run_in_executor(self._apply_filter_sync, image_bytes, filter_name)

    async def remove_background(self, image_bytes: bytes) -> bytes:
        async with self.http_client as client:
            response = await client.post(
                "https://api.remove.bg/v1.0/removebg",
                files={"image_file": image_bytes},
                headers={"X-Api-Key": "YOUR_REMOVEBG_API_KEY"}, 
            )
            response.raise_for_status()
            return response.content

    def _deepfry_sync(self, image_bytes: bytes) -> bytes:
        with Image.open(io.BytesIO(image_bytes)).convert("RGB") as img:
            img = img.filter(ImageFilter.SHARPEN)
            img = ImageOps.posterize(img, 4)
            img = ImageOps.colorize(ImageOps.grayscale(img), "#FF0000", "#FFFF00")
            output = io.BytesIO()
            img.save(output, "JPEG", quality=20)
            return output.getvalue()

    async def deepfry(self, image_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._deepfry_sync, image_bytes)

    def _convert_sticker_to_png_sync(self, sticker_bytes: bytes) -> bytes:
        with Image.open(io.BytesIO(sticker_bytes)) as img:
            output = io.BytesIO()
            img.save(output, format="PNG")
            return output.getvalue()

    async def convert_sticker_to_png(self, sticker_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._convert_sticker_to_png_sync, sticker_bytes)

    def _create_quote_sync(self, text: str, user_name: str, pfp_bytes: bytes = None, invert: bool = False) -> bytes:
        bg_color = (255, 255, 255) if invert else (21, 21, 21)
        text_color = (0, 0, 0) if invert else (255, 255, 255)
        name_color = (100, 100, 100) if invert else (150, 150, 150)
        
        pfp_size = 100
        padding = 20
        font_main_size = 40
        font_name_size = 30
        
        font_main = self._get_font(font_main_size)
        font_name = self._get_font(font_name_size)
        
        wrapped_text = "\n".join(textwrap.wrap(text, width=30))
        
        dummy_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        text_bbox = dummy_draw.textbbox((0, 0), wrapped_text, font=font_main)
        text_height = text_bbox[3] - text_bbox[1]
        text_width = text_bbox[2] - text_bbox[0]

        img_width = max(512, text_width + pfp_size + 3 * padding)
        img_height = max(150, text_height + 2 * padding)
        
        img = Image.new("RGB", (img_width, img_height), bg_color)
        draw = ImageDraw.Draw(img)
        
        if pfp_bytes:
            with Image.open(io.BytesIO(pfp_bytes)) as pfp:
                pfp = pfp.resize((pfp_size, pfp_size))
                img.paste(pfp, (padding, padding))
        
        text_x = padding + pfp_size + padding if pfp_bytes else padding
        draw.text((text_x, padding), wrapped_text, font=font_main, fill=text_color)
        
        name_bbox = draw.textbbox((0, 0), user_name, font=font_name)
        name_width = name_bbox[2] - name_bbox[0]
        draw.text((img_width - name_width - padding, img_height - 40), f"— {user_name}", font=font_name, fill=name_color)
        
        output = io.BytesIO()
        img.save(output, format="WEBP")
        return output.getvalue()
        
    async def create_quote(self, text: str, user_name: str, pfp_bytes: bytes = None, invert: bool = False) -> bytes:
        return await self._run_in_executor(self._create_quote_sync, text, user_name, pfp_bytes, invert)
        
    def _create_text_sticker_sync(self, text: str) -> bytes:
        lines = text.split("\n")
        font_size = 100
        font = self._get_font(font_size)
        
        dummy_draw = ImageDraw.Draw(Image.new("RGB", (1,1)))
        
        max_width = 0
        total_height = 0
        line_heights = []
        for line in lines:
            bbox = dummy_draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            max_width = max(max_width, line_width)
            total_height += line_height + 10
            line_heights.append(line_height)

        img = Image.new("RGBA", (max_width + 40, total_height + 10), (0,0,0,0))
        draw = ImageDraw.Draw(img)

        y = 20
        for i, line in enumerate(lines):
            bbox = dummy_draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (img.width - line_width) / 2
            draw.text((x, y), line, font=font, fill="white", stroke_width=2, stroke_fill="black")
            y += line_heights[i] + 10

        output = io.BytesIO()
        img.save(output, "WEBP")
        return output.getvalue()

    async def create_text_sticker(self, text: str) -> bytes:
        return await self._run_in_executor(self._create_text_sticker_sync, text)

    def _create_afk_card_sync(self, pfp_bytes: bytes, name: str, reason: str, duration: str) -> bytes:
        bg = Image.new("RGB", (800, 400), "#161616")
        draw = ImageDraw.Draw(bg)
        
        font_big = self._get_font(50)
        font_med = self._get_font(30)
        font_small = self._get_font(25)
        
        if pfp_bytes:
            with Image.open(io.BytesIO(pfp_bytes)) as pfp:
                pfp = pfp.resize((200, 200))
                bg.paste(pfp, (75, 100))
        
        draw.text((320, 80), name, font=font_big, fill="white")
        draw.line([(320, 140), (725, 140)], fill="#333", width=2)
        
        draw.text((320, 170), "Sedang AFK", font=font_med, fill="#aaa")
        
        wrapped_reason = "\n".join(textwrap.wrap(f"Alasan: {reason}", width=35))
        draw.text((320, 220), wrapped_reason, font=font_small, fill="white")
        
        draw.text((320, 310), f"Sejak: {duration} yang lalu", font=font_small, fill="#aaa")
        
        output = io.BytesIO()
        bg.save(output, format="PNG")
        return output.getvalue()
        
    async def create_afk_card(self, pfp_bytes: bytes, name: str, reason: str, duration: str) -> bytes:
        return await self._run_in_executor(self._create_afk_card_sync, pfp_bytes, name, reason, duration)

    def _create_profile_card_sync(self, pfp_bytes: bytes, name: str, username: str, user_id: int, bio: str, pfp_count: int, is_sudo: bool) -> bytes:
        bg = Image.new("RGB", (1000, 400), "#161616")
        draw = ImageDraw.Draw(bg)

        font_name = self._get_font(60)
        font_user = self._get_font(30)
        font_bio = self._get_font(25)
        font_stats = self._get_font(35)
        
        if pfp_bytes:
            with Image.open(io.BytesIO(pfp_bytes)) as pfp:
                pfp = pfp.resize((250, 250))
                bg.paste(pfp, (75, 75))

        draw.text((380, 70), name, font=font_name, fill="white")
        if is_sudo:
            draw.text((380, 145), f"@{username}  •  👑 Sudo User", font=font_user, fill="#aaa")
        else:
            draw.text((380, 145), f"@{username}", font=font_user, fill="#aaa")
        
        draw.line([(380, 190), (925, 190)], fill="#333", width=2)
        
        wrapped_bio = "\n".join(textwrap.wrap(bio or "Tidak ada bio.", width=45))
        draw.text((380, 210), wrapped_bio, font=font_bio, fill="white")

        draw.text((380, 310), str(pfp_count), font=font_stats, fill="white")
        draw.text((440, 310), str(user_id), font=font_stats, fill="white")
        
        draw.text((380, 350), "PFP", font=font_bio, fill="#aaa")
        draw.text((440, 350), "User ID", font=font_bio, fill="#aaa")
        
        output = io.BytesIO()
        bg.save(output, format="PNG")
        return output.getvalue()
        
    async def create_profile_card(self, pfp_bytes: bytes, name: str, username: str, user_id: int, bio: str, pfp_count: int, is_sudo: bool) -> bytes:
        return await self._run_in_executor(self._create_profile_card_sync, pfp_bytes, name, username, user_id, bio, pfp_count, is_sudo)

    def _invert_colors_sync(self, image_bytes: bytes) -> bytes:
        with Image.open(io.BytesIO(image_bytes)) as img:
            inverted_img = ImageOps.invert(img.convert("RGB"))
            output = io.BytesIO()
            inverted_img.save(output, format="PNG")
            return output.getvalue()

    async def invert_colors(self, image_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._invert_colors_sync, image_bytes)

    def _to_grayscale_sync(self, image_bytes: bytes) -> bytes:
        with Image.open(io.BytesIO(image_bytes)) as img:
            grayscale_img = ImageOps.grayscale(img)
            output = io.BytesIO()
            grayscale_img.save(output, format="PNG")
            return output.getvalue()

    async def to_grayscale(self, image_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._to_grayscale_sync, image_bytes)

    def _rotate_image_sync(self, image_bytes: bytes, angle: int) -> bytes:
        with Image.open(io.BytesIO(image_bytes)).convert("RGBA") as img:
            rotated_img = img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
            output = io.BytesIO()
            rotated_img.save(output, format="PNG")
            return output.getvalue()

    async def rotate_image(self, image_bytes: bytes, angle: int) -> bytes:
        return await self._run_in_executor(self._rotate_image_sync, image_bytes, angle)

    def _mirror_image_sync(self, image_bytes: bytes) -> bytes:
        with Image.open(io.BytesIO(image_bytes)) as img:
            mirrored_img = ImageOps.mirror(img)
            output = io.BytesIO()
            mirrored_img.save(output, format="PNG")
            return output.getvalue()

    async def mirror_image(self, image_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._mirror_image_sync, image_bytes)

    def _blur_image_sync(self, image_bytes: bytes, radius: int) -> bytes:
        with Image.open(io.BytesIO(image_bytes)) as img:
            blurred_img = img.filter(ImageFilter.GaussianBlur(radius=radius))
            output = io.BytesIO()
            blurred_img.save(output, format="PNG")
            return output.getvalue()

    async def blur_image(self, image_bytes: bytes, radius: int) -> bytes:
        return await self._run_in_executor(self._blur_image_sync, image_bytes, radius)

    def _sharpen_image_sync(self, image_bytes: bytes, factor: int) -> bytes:
        with Image.open(io.BytesIO(image_bytes)) as img:
            sharpened_img = img
            for _ in range(factor):
                sharpened_img = sharpened_img.filter(ImageFilter.SHARPEN)
            output = io.BytesIO()
            sharpened_img.save(output, format="PNG")
            return output.getvalue()
            
    async def sharpen_image(self, image_bytes: bytes, factor: int) -> bytes:
        return await self._run_in_executor(self._sharpen_image_sync, image_bytes, factor)
