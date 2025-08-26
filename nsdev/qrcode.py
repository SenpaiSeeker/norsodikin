import asyncio
import io

import qrcode


class QrCodeGenerator:
    def __init__(self):
        pass

    def _sync_generate(self, data: str):
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
