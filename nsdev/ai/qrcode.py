import asyncio
import colorsys
import io
import math
import random
from typing import Optional, Union

import qrcode
from PIL import Image, ImageDraw
from pyzbar import pyzbar
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import CircleModuleDrawer


class QrCodeGenerator:
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

    def _sync_generate(self, data: str, use_dots: bool, glow_background: bool) -> bytes:
        try:
            if not glow_background:
                qr_options = {
                    "version": 1,
                    "error_correction": qrcode.constants.ERROR_CORRECT_L,
                    "box_size": 10,
                    "border": 4,
                }
                qr = qrcode.QRCode(**qr_options)
                qr.add_data(data)
                qr.make(fit=True)

                image_factory = StyledPilImage if use_dots else None
                drawer_module = CircleModuleDrawer() if use_dots else None

                img = qr.make_image(image_factory=image_factory, module_drawer=drawer_module)

            else:
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
                qr.add_data(data)
                qr.make(fit=True)

                drawer = CircleModuleDrawer() if use_dots else None

                qr_img = qr.make_image(
                    image_factory=StyledPilImage, module_drawer=drawer, fill_color="black", back_color=(0, 0, 0, 0)
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
                img = background

            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            return img_bytes.getvalue()

        except Exception as e:
            raise e

    async def generate(self, data: str, use_dots: bool = True, glow_background: bool = True) -> bytes:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._sync_generate, data, use_dots, glow_background)
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
