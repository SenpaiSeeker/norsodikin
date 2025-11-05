import asyncio
import colorsys
import io
import math
import random
from typing import Optional, Union

import qrcode
from PIL import Image, ImageDraw, ImageFont
from pyzbar import pyzbar
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import CircleModuleDrawer

from ..utils.font_manager import FontManager


class QrCodeGenerator(FontManager):
    def __init__(self):
        super().__init__()

    def _sync_create_glow_background(self, size: int, color: tuple) -> Image.Image:
        background = Image.new("RGB", (size, size))
        draw = ImageDraw.Draw(background)

        center_x, center_y = size / 2, size / 2
        max_dist = math.sqrt(center_x**2 + center_y**2)

        for y in range(size):
            for x in range(size):
                distance = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                ratio = distance / max_dist
                intensity = max(0, 1 - ratio**2)
                r = int(color[0] * intensity)
                g = int(color[1] * intensity)
                b = int(color[2] * intensity)
                draw.point((x, y), fill=(r, g, b))
        return background

    def _sync_generate(
        self,
        data: str,
        use_dots: bool,
        glow_background: bool,
        bottom_text: Optional[str] = None,
        creator_text: Optional[str] = None,
    ) -> bytes:
        try:
            qr_options = {
                "version": 1,
                "error_correction": qrcode.constants.ERROR_CORRECT_H,
                "box_size": 10,
                "border": 4,
            }
            qr = qrcode.QRCode(**qr_options)
            qr.add_data(data)
            qr.make(fit=True)

            image_factory = StyledPilImage if use_dots else None
            drawer_module = CircleModuleDrawer() if use_dots else None

            if not glow_background:
                img = qr.make_image(image_factory=image_factory, module_drawer=drawer_module, fill_color="black", back_color="white")
            else:
                qr_img = qr.make_image(
                    image_factory=StyledPilImage, module_drawer=drawer_module, fill_color="black", back_color=(0, 0, 0, 0)
                ).convert("RGBA")

                qr_size = qr_img.size[0]
                padding = qr_size // 5
                bg_size = qr_size + padding * 2

                hue = random.random()
                saturation = 0.95
                value = 1.0
                rgb_float = colorsys.hsv_to_rgb(hue, saturation, value)
                glow_color = tuple(int(c * 255) for c in rgb_float)

                background = self._sync_create_glow_background(bg_size, glow_color)
                paste_position = (padding, padding)
                background.paste(qr_img, paste_position, qr_img)
                img = background.convert("RGB")

            if not bottom_text and not creator_text:
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                return img_bytes.getvalue()

            qr_w, qr_h = img.size
            padding_top = 40
            padding_between_qr_button = 30
            padding_between_button_creator = 20
            padding_bottom = 40
            
            font_button = self._get_font_from_package("NotoSans-Bold.ttf", 30)
            font_creator = self._get_font_from_package("NotoSans-Bold.ttf", 40)
            
            button_h, creator_h = 0, 0
            
            if bottom_text:
                button_h = 60
                
            if creator_text:
                bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), creator_text, font=font_creator)
                creator_h = bbox[3] - bbox[1]

            total_h = (
                padding_top + qr_h + padding_between_qr_button + button_h + 
                padding_between_button_creator + creator_h + padding_bottom
            )
            
            final_canvas = Image.new("RGB", (qr_w, total_h), "#F0F0F0")
            draw = ImageDraw.Draw(final_canvas)
            
            final_canvas.paste(img, (0, padding_top))
            
            current_y = padding_top + qr_h
            
            if bottom_text:
                current_y += padding_between_qr_button
                bbox = draw.textbbox((0, 0), bottom_text, font=font_button)
                button_text_w = bbox[2] - bbox[0]
                
                button_w = button_text_w + 80
                button_x = (qr_w - button_w) / 2
                
                draw.rounded_rectangle(
                    (button_x, current_y, button_x + button_w, current_y + button_h),
                    radius=30, fill="#F0F0F0", outline="black", width=4
                )
                
                text_x = button_x + (button_w - button_text_w) / 2
                text_y = current_y + (button_h - (bbox[3] - bbox[1])) / 2
                draw.text((text_x, text_y), bottom_text, font=font_button, fill="black")
                current_y += button_h

            if creator_text:
                current_y += padding_between_button_creator
                bbox = draw.textbbox((0, 0), creator_text, font=font_creator)
                creator_w = bbox[2] - bbox[0]
                text_x = (qr_w - creator_w) / 2
                
                shadow_color = "black"
                for offset in [(2, 2), (-2, 2), (2, -2), (-2, -2)]:
                    draw.text((text_x + offset[0], current_y + offset[1]), creator_text, font=font_creator, fill=shadow_color)
                
                draw.text((text_x, current_y), creator_text, font=font_creator, fill="white")

            img_bytes = io.BytesIO()
            final_canvas.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            return img_bytes.getvalue()

        except Exception as e:
            raise e

    async def generate(
        self,
        data: str,
        use_dots: bool = True,
        glow_background: bool = False,
        bottom_text: Optional[str] = None,
        creator_text: Optional[str] = None,
    ) -> bytes:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, self._sync_generate, data, use_dots, glow_background, bottom_text, creator_text
        )
        if isinstance(result, Exception):
            raise result
        return result

    def _sync_read(self, image_data: Union[str, bytes, io.BytesIO]) -> Optional[str]:
        try:
            image = Image.open(image_data)
            decoded_objects = pyzbar.decode(image)
            if not decoded_objects:
                return None
            return decoded_objects[0].data.decode("utf-8")
        except Exception as e:
            raise e

    async def read(self, image_data: Union[str, bytes, io.BytesIO]) -> Optional[str]:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._sync_read, image_data)
        if isinstance(result, Exception):
            raise result
        return result
