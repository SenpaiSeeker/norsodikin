import asyncio
import os
import random
import urllib.request
from functools import partial
from io import BytesIO
from typing import List, Tuple

import requests
from PIL import Image, ImageDraw, ImageFont


class ImageManipulator:
    def __init__(self):
        self.font_cache_dir = ".cache_fonts"
        os.makedirs(self.font_cache_dir, exist_ok=True)

        try:
            local_fonts = [
                os.path.join(self.font_cache_dir, f)
                for f in os.listdir(self.font_cache_dir)
                if f.lower().endswith((".ttf", ".otf")) and os.path.isfile(os.path.join(self.font_cache_dir, f))
            ]
        except Exception:
            local_fonts = []

        if local_fonts:
            self.available_fonts = local_fonts
        else:
            font_urls = self._fetch_google_font_urls()
            self.available_fonts = self._ensure_local_fonts(font_urls)
    
    def _fetch_google_font_urls(self, limit: int = 15) -> List[str]:
        all_font_families = []
        base_dirs = ["ofl", "apache"]
        api_base_url = "https://api.github.com/repos/google/fonts/contents/"
        try:
            for dir_name in base_dirs:
                response = requests.get(f"{api_base_url}{dir_name}", timeout=10)
                response.raise_for_status()
                all_font_families.extend(
                    [item for item in response.json() if isinstance(item, dict) and item.get("type") == "dir"]
                )
            if not all_font_families: return []
            random.shuffle(all_font_families)
            selected_families = all_font_families[:limit]
            font_urls = []
            for family in selected_families:
                try:
                    family_response = requests.get(family["url"], timeout=10)
                    family_response.raise_for_status()
                    font_files = family_response.json()
                    if not isinstance(font_files, list): continue
                    regular_match, any_ttf_match = None, None
                    for font_file in font_files:
                        if isinstance(font_file, dict) and font_file.get("type") == "file":
                            name = font_file.get("name", "").lower()
                            if "regular" in name and name.endswith(".ttf"):
                                regular_match = font_file; break
                            if any_ttf_match is None and name.endswith(".ttf"):
                                any_ttf_match = font_file
                    best_match = regular_match or any_ttf_match
                    if best_match and best_match.get("download_url"):
                        font_urls.append(best_match["download_url"])
                except requests.RequestException: continue
            return font_urls
        except requests.RequestException: return []

    def _ensure_local_fonts(self, urls: List[str]) -> List[str]:
        paths: List[str] = []
        for u in urls:
            try:
                name = os.path.basename(urllib.parse.urlparse(u).path)
                if not name: continue
                local_path = os.path.join(self.font_cache_dir, name)
                if os.path.isfile(local_path) and os.path.getsize(local_path) > 1024:
                    paths.append(local_path)
                    continue
                try:
                    urllib.request.urlretrieve(u, local_path)
                    if os.path.isfile(local_path) and os.path.getsize(local_path) > 1024:
                        paths.append(local_path)
                except Exception: continue
            except Exception: continue
        return paths

    def _get_font(self, font_size: int):
        if hasattr(self, 'available_fonts') and self.available_fonts:
            random_font_path = random.choice(self.available_fonts)
            try:
                return ImageFont.truetype(random_font_path, font_size)
            except IOError:
                pass
        return ImageFont.load_default()

    def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, partial(func, *args, **kwargs))

    def _sync_add_watermark(self, image_bytes: bytes, text: str, position: Tuple[int, int] = (10, 10), font_size: int = 30, opacity: int = 128) -> bytes:
        img = Image.open(BytesIO(image_bytes)).convert("RGBA")
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        
        font = self._get_font(font_size)
            
        draw = ImageDraw.Draw(txt_layer)
        draw.text(position, text, font=font, fill=(255, 255, 255, opacity))
        
        watermarked_img = Image.alpha_composite(img, txt_layer)
        
        output_buffer = BytesIO()
        watermarked_img.save(output_buffer, format="PNG")
        return output_buffer.getvalue()

    async def add_watermark(self, image_bytes: bytes, text: str, position: Tuple[int, int] = (10, 10), font_size: int = 30, opacity: int = 128) -> bytes:
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
