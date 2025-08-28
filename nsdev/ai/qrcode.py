import asyncio
import io
from typing import Optional, Union

import qrcode
from PIL import Image
from pyzbar import pyzbar


class QrCodeGenerator:
    def _sync_generate(self, data: str) -> bytes:
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            return img_bytes.getvalue()
        except Exception as e:
            return e

    async def generate(self, data: str) -> bytes:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._sync_generate, data)
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
            return e

    async def read(self, image_data: Union[str, bytes, io.BytesIO]) -> Optional[str]:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._sync_read, image_data)

        if isinstance(result, Exception):
            # Jika terjadi error saat membaca gambar, lempar exception
            raise result

        return result
