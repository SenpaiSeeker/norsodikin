import asyncio
import base64
import random
import textwrap
from functools import partial
from importlib import resources
from io import BytesIO
from typing import Tuple

from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from playwright.async_api import async_playwright

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

    async def _render_html_with_playwright(self, html_content: str, width: int) -> bytes:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": width, "height": 100})
            await page.set_content(html_content)
            
            element_handle = await page.query_selector('.container')
            if not element_handle:
                await browser.close()
                raise RuntimeError("Could not find the '.container' element to screenshot.")

            screenshot_bytes = await element_handle.screenshot(type="png", omit_background=True)
            await browser.close()
            return screenshot_bytes

    def _sync_create_quote(self, text: str, user_name: str, pfp_bytes: bytes, invert: bool) -> bytes:
        return asyncio.run(self._async_create_quote(text, user_name, pfp_bytes, invert))

    async def _async_create_quote(self, text: str, user_name: str, pfp_bytes: bytes, invert: bool) -> bytes:
        if pfp_bytes:
            pfp_base64 = "data:image/png;base64," + base64.b64encode(pfp_bytes).decode()
        else:
            initial = user_name[0].upper() if user_name else "U"
            default_pfp_bytes = self._get_default_pfp(initial)
            pfp_base64 = "data:image/png;base64," + base64.b64encode(default_pfp_bytes).decode()

        bg_color, text_color, name_color = (
            ("#161616", "#FFFFFF", "#AAAAAA") if not invert else ("#FFFFFF", "#161616", "#555555")
        )
        link_color = "#88C0D0" if not invert else "#3B82F6"

        soup = BeautifulSoup(text, "html.parser")
        for tag in soup.find_all("a"):
            tag.name = "span"
            tag["style"] = f"color: {link_color};"

        clean_html = str(soup).replace("\n", "<br>")

        html_template = """
        <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap');
                body {{
                    margin: 0;
                    width: 800px;
                }}
                .container {{
                    font-family: 'Noto Sans', sans-serif;
                    background: {bg_color};
                    color: {text_color};
                    padding: 40px;
                    display: flex;
                    align-items: flex-start;
                }}
                .pfp {{
                    width: 100px;
                    height: 100px;
                    border-radius: 50%;
                    object-fit: cover;
                    margin-right: 25px;
                    flex-shrink: 0;
                }}
                .text-content {{
                    display: flex;
                    flex-direction: column;
                }}
                .name {{
                    font-size: 28px;
                    font-weight: 700;
                    color: {name_color};
                    margin-bottom: 10px;
                }}
                .quote {{
                    font-size: 36px;
                    line-height: 1.4;
                    word-wrap: break-word;
                    word-break: break-word;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <img src="{pfp_base64}" class="pfp" />
                <div class="text-content">
                    <div class="name">{user_name}</div>
                    <div class="quote">{clean_html}</div>
                </div>
            </div>
        </body>
        </html>
        """.format(
            bg_color=bg_color,
            text_color=text_color,
            name_color=name_color,
            pfp_base64=pfp_base64,
            user_name=user_name,
            clean_html=clean_html,
        )

        image_bytes = await self._render_html_with_playwright(html_template, 800)
        
        output = BytesIO()
        Image.open(BytesIO(image_bytes)).save(output, 'WEBP')
        return output.getvalue()

    async def create_quote(self, text: str, user_name: str, pfp_bytes: bytes, invert: bool = False) -> bytes:
        return await self._async_create_quote(text, user_name, pfp_bytes, invert)

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

        font_size = int(img.width / 15)
        font = self._get_font(font_size)
        draw = ImageDraw.Draw(txt_layer)

        random_color = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255), opacity)
        outline_color = (0, 0, 0, opacity)

        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x = (img.width - text_width) / 2
        y = (img.height - text_height) / 2

        for offset_x in range(-2, 3):
            for offset_y in range(-2, 3):
                if offset_x != 0 or offset_y != 0:
                    draw.text((x + offset_x, y + offset_y), text, font=font, fill=outline_color)

        draw.text((x, y), text, font=font, fill=random_color)

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
        opacity: int = 200,
    ) -> bytes:
        return await self._run_in_executor(self._sync_add_watermark, image_bytes, text, position, font_size, opacity)

    def _sync_resize(self, image_bytes: bytes, size: Tuple[int, int], keep_aspect_ratio: bool = True) -> bytes:
        img = Image.open(BytesIO(image_bytes))
        if keep_aspect_ratio:
            img.thumbnail(size, Image.Resampling.LANCZOS)
        else:
            img = img.resize(size, Image.Resampling.LANCZOS)
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
            grayscale_img = grayscale_img.convert("RGB")
            processed_img = grayscale_img
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

    def _sync_create_profile_card(
        self, pfp_bytes: bytes, name: str, username: str, user_id: int, bio: str, pfp_count: int, is_sudo: bool
    ) -> bytes:
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

        font_name = self._get_font_from_package("NotoSans-Bold.ttf", 48)
        font_user = self._get_font_from_package("NotoSans-Regular.ttf", 32)
        font_bio = self._get_font_from_package("NotoSans-Italic.ttf", 28)
        font_stats = self._get_font_from_package("NotoSans-Regular.ttf", 24)
        font_badge = self._get_font_from_package("NotoSans-Bold.ttf", 20)

        img.paste(pfp, (50, 50), pfp)

        text_x = 300
        draw.text((text_x, 70), name, font=font_name, fill="#C9D1D9")

        username_text = f"@{username} | ID: {user_id}" if username else f"ID: {user_id}"
        draw.text((text_x, 130), username_text, font=font_user, fill="#8B949E")

        if is_sudo:
            badge_bbox = draw.textbbox((0, 0), "SUDO", font=font_badge)
            badge_w = badge_bbox[2] - badge_bbox[0] + 20
            badge_h = badge_bbox[3] - badge_bbox[1] + 10
            name_bbox = draw.textbbox((0, 0), name, font=font_name)
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

    async def create_profile_card(
        self, pfp_bytes: bytes, name: str, username: str, user_id: int, bio: str, pfp_count: int, is_sudo: bool
    ) -> bytes:
        return await self._run_in_executor(
            self._sync_create_profile_card, pfp_bytes, name, username, user_id, bio, pfp_count, is_sudo
        )

    def _sync_create_text_sticker(self, text: str) -> bytes:
        clean_text = BeautifulSoup(text, "html.parser").get_text()
        font = self._get_font_from_package("NotoSans-Bold.ttf", 90)

        dummy_img = Image.new("RGBA", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)

        bbox = dummy_draw.textbbox((0, 0), clean_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        padding = 30
        canvas_width = text_width + (padding * 2)
        canvas_height = text_height + (padding * 2)

        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        shadow_color = (0, 0, 0, 100)
        text_color = (255, 255, 255)

        draw.text((padding + 3, padding + 3), clean_text, font=font, fill=shadow_color)
        draw.text((padding, padding), clean_text, font=font, fill=text_color)

        if canvas.width > canvas.height:
            if canvas.width > 512:
                canvas.thumbnail((512, 512), Image.Resampling.LANCZOS)
        else:
            if canvas.height > 512:
                canvas.thumbnail((512, 512), Image.Resampling.LANCZOS)

        output_buffer = BytesIO()
        canvas.save(output_buffer, format="WEBP")
        return output_buffer.getvalue()

    async def create_text_sticker(self, text: str) -> bytes:
        return await self._run_in_executor(self._sync_create_text_sticker, text)

    def _invert_colors_sync(self, image_bytes: bytes) -> bytes:
        with Image.open(BytesIO(image_bytes)) as img:
            inverted_img = ImageOps.invert(img.convert("RGB"))
            output = BytesIO()
            inverted_img.save(output, format="PNG")
            return output.getvalue()

    async def invert_colors(self, image_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._invert_colors_sync, image_bytes)

    def _to_grayscale_sync(self, image_bytes: bytes) -> bytes:
        with Image.open(BytesIO(image_bytes)) as img:
            grayscale_img = ImageOps.grayscale(img)
            output = BytesIO()
            grayscale_img.save(output, format="PNG")
            return output.getvalue()

    async def to_grayscale(self, image_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._to_grayscale_sync, image_bytes)

    def _rotate_image_sync(self, image_bytes: bytes, angle: int) -> bytes:
        with Image.open(BytesIO(image_bytes)).convert("RGBA") as img:
            rotated_img = img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
            output = BytesIO()
            rotated_img.save(output, format="PNG")
            return output.getvalue()

    async def rotate_image(self, image_bytes: bytes, angle: int) -> bytes:
        return await self._run_in_executor(self._rotate_image_sync, image_bytes, angle)

    def _mirror_image_sync(self, image_bytes: bytes) -> bytes:
        with Image.open(BytesIO(image_bytes)) as img:
            mirrored_img = ImageOps.mirror(img)
            output = BytesIO()
            mirrored_img.save(output, format="PNG")
            return output.getvalue()

    async def mirror_image(self, image_bytes: bytes) -> bytes:
        return await self._run_in_executor(self._mirror_image_sync, image_bytes)

    def _blur_image_sync(self, image_bytes: bytes, radius: int) -> bytes:
        with Image.open(BytesIO(image_bytes)) as img:
            blurred_img = img.filter(ImageFilter.GaussianBlur(radius=radius))
            output = BytesIO()
            blurred_img.save(output, format="PNG")
            return output.getvalue()

    async def blur_image(self, image_bytes: bytes, radius: int) -> bytes:
        return await self._run_in_executor(self._blur_image_sync, image_bytes, radius)

    def _sharpen_image_sync(self, image_bytes: bytes, factor: int) -> bytes:
        with Image.open(BytesIO(image_bytes)) as img:
            sharpened_img = img
            for _ in range(factor):
                sharpened_img = sharpened_img.filter(ImageFilter.SHARPEN)
            output = BytesIO()
            sharpened_img.save(output, format="PNG")
            return output.getvalue()

    async def sharpen_image(self, image_bytes: bytes, factor: int) -> bytes:
        return await self._run_in_executor(self._sharpen_image_sync, image_bytes, factor)
