import asyncio
from io import BytesIO
import httpx
import uuid
import random

class ImageInpainter:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
        ]

    async def remove_watermark(self, image_bytes: bytes) -> bytes:
        return await self._remove_via_pixelbin(image_bytes)

    async def _remove_via_pixelbin(self, image_bytes: bytes) -> bytes:
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Origin": "https://www.watermarkremover.io",
            "Referer": "https://www.watermarkremover.io/",
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }
        
        files_data = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="image"; filename="image.jpg"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode("utf-8") + image_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(
                    "https://api.pixelbin.io/v2/remove-watermark",
                    content=files_data,
                    headers=headers
                )
                response.raise_for_status()
                
                response_data = response.json()
                if not response_data.get("url"):
                    raise ValueError("API tidak mengembalikan URL gambar hasil.")
                    
                result_url = response_data["url"]
                
                img_response = await client.get(result_url)
                img_response.raise_for_status()
                
                return img_response.content
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403 or e.response.status_code == 401:
                    raise ValueError(f"Gagal mengakses API (Blokir/Auth): {e}")
                raise e
            except Exception as e:
                raise ValueError(f"Gagal memproses penghapusan watermark: {e}")
