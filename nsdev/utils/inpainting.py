import asyncio
import uuid
import random
import json
import httpx

class ImageInpainter:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        ]

    async def remove_watermark(self, image_bytes: bytes) -> bytes:
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Origin": "https://dewatermark.ai",
            "Referer": "https://dewatermark.ai/",
        }

        async with httpx.AsyncClient(timeout=120) as client:
            files = {'file': ('image.jpg', image_bytes, 'image/jpeg')}
            
            try:
                upload_resp = await client.post(
                    "https://api.dewatermark.ai/api/image-upload", 
                    files=files, 
                    headers=headers
                )
                upload_resp.raise_for_status()
                upload_data = upload_resp.json()
                
                if "code" in upload_data and upload_data["code"] != 0:
                    raise ValueError(f"Upload gagal: {upload_data}")
                    
                image_url = upload_data["data"]["url"]
                uid = upload_data["data"]["uid"]
                
                process_payload = {"url": image_url, "uid": uid}
                process_resp = await client.post(
                    "https://api.dewatermark.ai/api/remove-watermark",
                    json=process_payload,
                    headers=headers
                )
                process_resp.raise_for_status()
                
                proc_data = process_resp.json()
                if "code" in proc_data and proc_data["code"] != 0:
                     raise ValueError(f"Proses gagal: {proc_data}")

                result_url = proc_data["data"]["url"]
                
                final_img = await client.get(result_url)
                final_img.raise_for_status()
                
                return final_img.content

            except Exception:
                return await self._fallback_remove(image_bytes)

    async def _fallback_remove(self, image_bytes: bytes) -> bytes:
        async with httpx.AsyncClient(timeout=60) as client:
             files = {'file': ('image.jpg', image_bytes, 'image/jpeg')}
             try:
                 response = await client.post(
                     "https://zhn.top/api/removeWatermark",
                     files=files
                 )
                 response.raise_for_status()
                 
                 if response.headers.get('content-type', '').startswith('image/'):
                     return response.content
                 
                 data = response.json()
                 if 'url' in data:
                     res = await client.get(data['url'])
                     return res.content
                     
                 raise ValueError("Fallback gagal")
             except Exception as e:
                 raise ValueError(f"Semua metode gagal. Error: {e}")
