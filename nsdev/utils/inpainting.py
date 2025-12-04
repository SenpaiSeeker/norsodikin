import asyncio
import base64
import json
import aiohttp
from typing import Optional

class ImageInpainter:
    def __init__(self):
        self.api_url = "https://fdguigo-remove-watermark.hf.space/run/predict"

    async def remove_watermark(self, image_bytes: bytes) -> bytes:
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:image/jpeg;base64,{b64_image}"

        payload = {
            "data": [
                data_uri
            ]
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.api_url, json=payload, timeout=60) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API Error {response.status}: {error_text}")

                    result = await response.json()
                    data_list = result.get("data", [])

                    if not data_list:
                        raise Exception("API tidak mengembalikan data gambar.")

                    result_uri = data_list[0]
                    if "," in result_uri:
                        base64_data = result_uri.split(",")[1]
                    else:
                        base64_data = result_uri

                    return base64.b64decode(base64_data)

            except asyncio.TimeoutError:
                raise Exception("Waktu habis saat menghubungi server AI penghapus watermark.")
            except Exception as e:
                raise Exception(f"Gagal menghapus watermark: {e}")
