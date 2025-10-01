import asyncio
import random
import textwrap
from functools import partial
from importlib import resources
from io import BytesIO
from typing import Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

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
            sepia_palette = [
                component
                for i in range(256)
                for component in (int(min(255, i * 1.2)), int(min(255, i * 1.0)), int(min(255, i * 0.8)))
            ]
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

    def _get_default_pfp(self, initial: str) -> bytes:
        W, H = (200, 200)
        bg_color = (120, 120, 120)
        img = Image.new("RGB", (W, H), color=bg_color)

        font = self._get_font(100)
        draw = ImageDraw.Draw(img)

        bbox = draw.textbbox((0, 0), initial, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        position = ((W - text_w) / 2, (H - text_h) / 2 - 10)
        draw.text(position, initial, font=font, fill=(255, 255, 255))

        output = BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()

    def _sync_create_quote(self, text: str, user_name: str, pfp_bytes: bytes, invert: bool) -> bytes:
        pfp_data = pfp_bytes
        if not pfp_data:
            initial = user_name[0].upper()
            pfp_data = self._get_default_pfp(initial)

        pfp = Image.open(BytesIO(pfp_data)).convert("RGBA")
        pfp = pfp.resize((120, 120))

        mask = Image.new("L", pfp.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + pfp.size, fill=255)
        pfp.putalpha(mask)

        with resources.as_file(resources.files("assets").joinpath("fonts", "NotoSans-Regular.ttf")) as font_path:
            font_name_path = str(font_path)
        with resources.as_file(resources.files("assets").joinpath("fonts", "NotoColorEmoji-Regular.ttf")) as font_path:
            emoji_font_path = str(font_path)
        with resources.as_file(
            resources.files("assets").joinpath("fonts", "NotoSansSymbols2-Regular.ttf")
        ) as font_path:
            symbol_font_path = str(font_path)

        font_paths = [font_name_path, emoji_font_path, symbol_font_path]

        layout_engine = ImageFont.Layout.RAQM
        font_name = ImageFont.truetype(font_name_path, 40, layout_engine=layout_engine)
        font_quote = ImageFont.truetype(font_name_path, 50, layout_engine=layout_engine)

        bg_color, text_color, name_color = (
            ("#161616", "#FFFFFF", "#AAAAAA") if not invert else ("#FFFFFF", "#161616", "#555555")
        )

        TEXT_LEFT, PADDING_RIGHT, MAX_WIDTH, MIN_WIDTH = 200, 80, 1280, 512
        MAX_TEXT_WIDTH = MAX_WIDTH - TEXT_LEFT - PADDING_RIGHT

        final_lines = []
        for line in text.splitlines():
            words = (line if line else " ").split(" ")
            current_line = ""
            for word in words:
                test_line = (current_line + " " + word).strip()
                if font_quote.getlength(test_line) > MAX_TEXT_WIDTH:
                    final_lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            final_lines.append(current_line)

        longest_line_width = 0
        for line in final_lines:
            line_width = font_quote.getlength(line)
            if line_width > longest_line_width:
                longest_line_width = line_width

        name_width = font_name.getlength(user_name)
        longest_line_width = max(longest_line_width, name_width)

        image_w = min(MAX_WIDTH, max(MIN_WIDTH, int(TEXT_LEFT + longest_line_width + PADDING_RIGHT)))

        def get_line_height(font, text_line):
            if not text_line.strip():
                bbox = font.getbbox("Tg")
                return bbox[3] * 0.5
            bbox = font.getbbox(text_line)
            return bbox[3] - bbox[1]

        line_height_name = get_line_height(font_name, user_name)
        line_spacing_quote = 15
        total_quote_h = (
            sum([get_line_height(font_quote, l) for l in final_lines]) + (len(final_lines) - 1) * line_spacing_quote
        )

        PADDING_TOP_BOTTOM = 60
        image_h = max(200, int(total_quote_h + line_height_name + 20 + PADDING_TOP_BOTTOM * 2))

        img = Image.new("RGB", (image_w, image_h), bg_color)
        draw = ImageDraw.Draw(img)
        img.paste(pfp, (50, 60), pfp)

        current_h = (image_h - (total_quote_h + line_height_name + 20)) / 2

        draw.text(
            (TEXT_LEFT, current_h),
            user_name,
            font=font_name,
            fill=name_color,
            features=["-liga"],
            font_features=font_paths,
        )
        current_h += line_height_name + 20

        for line in final_lines:
            draw.text(
                (TEXT_LEFT, current_h),
                line,
                font=font_quote,
                fill=text_color,
                features=["-liga"],
                font_features=font_paths,
            )
            current_h += get_line_height(font_quote, line) + line_spacing_quote

        output = BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()

    async def create_quote(self, text: str, user_name: str, pfp_bytes: bytes, invert: bool = False) -> bytes:
        return await self._run_in_executor(self._sync_create_quote, text, user_name, pfp_bytes, invert)

    def _sync_deepfry(self, image_bytes: bytes) -> bytes:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        img = ImageEnhance.Color(img).enhance(3.0)
        img = ImageEnhance.Contrast(img).enhance(2.5)
        img = ImageEnhance.Sharpness(img).enhance(3.0)

        noise = Image.new("RGB", img.size)
        draw = ImageDraw.Draw(noise)
        for y in range(img.height):
            for x in range(img.width):
                draw.point((x, y), (random.randint(0, 50), random.randint(0, 50), random.randint(0, 50)))
        img = Image.blend(img, noise, 0.15)

        output_buffer = BytesIO()
        img.save(output_buffer, format="JPEG", quality=80)
        return output_buffer.getvalue()

    async def deepfry(self, image_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._sync_deepfry, image_bytes)
        
    def _sync_create_afk_card(self, pfp_bytes: bytes, name: str, reason: str, duration: str) -> bytes:
        pfp_data = pfp_bytes
        if not pfp_data:
            initial = name[0].upper() if name else "U"
            pfp_data = self._get_default_pfp(initial)
        
        pfp = Image.open(BytesIO(pfp_data)).convert("RGBA").resize((128, 128))
        mask = Image.new("L", pfp.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + pfp.size, fill=255)
        pfp.putalpha(mask)

        W, H = 800, 300
        img = Image.new("RGB", (W, H), "#1C1C1E")
        draw = ImageDraw.Draw(img)

        font_name = self._get_font_from_package("NotoSans-Bold.ttf", 36)
        font_status = self._get_font_from_package("NotoSans-Bold.ttf", 28)
        font_text = self._get_font_from_package("NotoSans-Regular.ttf", 24)

        img.paste(pfp, (40, (H - 128) // 2), pfp)

        text_x = 200
        draw.text((text_x, 60), name, font=font_name, fill="#FFFFFF")
        draw.text((text_x, 110), "SEDANG AFK", font=font_status, fill="#FF9500")
        
        if reason:
            draw.text((text_x, 170), f"Alasan: {reason}", font=font_text, fill="#EBEBF599")
        
        draw.text((text_x, 200), f"Sejak: {duration}", font=font_text, fill="#EBEBF599")

        output = BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()
        
    async def create_afk_card(self, pfp_bytes: bytes, name: str, reason: str, duration: str) -> bytes:
        return await self._run_in_executor(self._sync_create_afk_card, pfp_bytes, name, reason, duration)

    def _sync_create_profile_card(self, pfp_bytes: bytes, name: str, username: str, user_id: int, bio: str, pfp_count: int, is_sudo: bool) -> bytes:
        pfp_data = pfp_bytes
        if not pfp_data:
            initial = name[0].upper() if name else "U"
            pfp_data = self._get_default_pfp(initial)
        
        pfp = Image.open(BytesIO(pfp_data)).convert("RGBA").resize((200, 200))
        mask = Image.new("L", pfp.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + pfp.size, fill=255)
        pfp.putalpha(mask)

        W, H = 900, 500
        img = Image.new("RGB", (W, H), "#161B22")
        draw = ImageDraw.Draw(img)
        
        font_name_path = self._get_font_from_package("NotoSans-Bold.ttf", 48).path
        font_user_path = self._get_font_from_package("NotoSans-Regular.ttf", 32).path
        font_bio_path = self._get_font_from_package("NotoSans-Italic.ttf", 28).path
        font_stats_path = self._get_font_from_package("NotoSans-Regular.ttf", 24).path
        font_badge_path = self._get_font_from_package("NotoSans-Bold.ttf", 20).path
        font_symbol_path = self._get_font_from_package("NotoSansSymbols2-Regular.ttf", 48).path
        
        font_name = ImageFont.truetype(font_symbol_path, 48)
        font_user = ImageFont.truetype(font_user_path, 32)
        font_bio = ImageFont.truetype(font_bio_path, 28)
        font_stats = ImageFont.truetype(font_stats_path, 24)
        font_badge = ImageFont.truetype(font_badge_path, 20)
        
        img.paste(pfp, (50, 50), pfp)

        text_x = 300
        draw.text((text_x, 70), name, font=font_name, fill="#C9D1D9")
        
        username_text = f"@{username} | ID: {user_id}" if username else f"ID: {user_id}"
        draw.text((text_x, 130), username_text, font=font_user, fill="#8B949E")

        if is_sudo:
            badge_bbox = draw.textbbox((0,0), "SUDO", font=font_badge)
            badge_w = badge_bbox[2] - badge_bbox[0] + 20
            badge_h = badge_bbox[3] - badge_bbox[1] + 10
            name_bbox = draw.textbbox((0,0), name, font=font_name)
            badge_x = text_x + (name_bbox[2] - name_bbox[0]) + 15
            badge_y = 75
            draw.rounded_rectangle((badge_x, badge_y, badge_x + badge_w, badge_y + badge_h), radius=5, fill="#388E3C")
            draw.text((badge_x + 10, badge_y + 5), "SUDO", font=font_badge, fill="#FFFFFF")

        draw.line([(50, 280), (W - 50, 280)], fill="#30363D", width=2)

        wrapped_bio = textwrap.wrap(bio, width=45) if bio else ["Tidak ada bio."]
        bio_y = 310
        for line in wrapped_bio[:3]:
            draw.text((50, bio_y), line, font=font_bio, fill="#C9D1D9")
            bio_y += 35

        draw.text((50, H - 70), f"Total Foto Profil: {pfp_count}", font=font_stats, fill="#8B949E")
        
        output = BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()

    async def create_profile_card(self, pfp_bytes: bytes, name: str, username: str, user_id: int, bio: str, pfp_count: int, is_sudo: bool) -> bytes:
        return await self._run_in_executor(self._sync_create_profile_card, pfp_bytes, name, username, user_id, bio, pfp_count, is_sudo)
