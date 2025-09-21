import os
import random
import urllib.parse
import urllib.request
from typing import List

import requests
from PIL import Image, ImageDraw, ImageFont


class FontManager:
    def __init__(self):
        self.font_cache_dir = ".cache_fonts"
        os.makedirs(self.font_cache_dir, exist_ok=True)
        self.available_fonts = self._load_or_fetch_fonts()

    def _get_default_pfp(self, initial: str) -> bytes:
        from io import BytesIO
        
        W, H = (200, 200)
        bg_color = (120, 120, 120)
        img = Image.new('RGB', (W, H), color=bg_color)
        
        font = self._get_font(100)
        draw = ImageDraw.Draw(img)
        
        bbox = draw.textbbox((0, 0), initial, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        position = ((W-text_w)/2, (H-text_h)/2 - 10)
        draw.text(position, initial, font=font, fill=(255, 255, 255))
        
        output = BytesIO()
        img.save(output, format='PNG')
        return output.getvalue()

    def _load_or_fetch_fonts(self) -> List[str]:
        try:
            font_extensions = (".ttf", ".otf")
            local_fonts = [
                os.path.join(self.font_cache_dir, f)
                for f in os.listdir(self.font_cache_dir)
                if f.lower().endswith(font_extensions) and os.path.isfile(os.path.join(self.font_cache_dir, f))
            ]
            if local_fonts:
                return local_fonts
        except Exception:
            pass
        font_urls = self._fetch_google_font_urls()
        return self._ensure_local_fonts(font_urls)

    def _fetch_google_font_urls(self, limit: int = 30) -> List[str]:
        all_font_families = []
        base_dirs = ["ofl", "apache", "ufl"]
        api_base_url = "https://api.github.com/repos/google/fonts/contents/"
        try:
            for dir_name in base_dirs:
                response = requests.get(f"{api_base_url}{dir_name}", timeout=10)
                response.raise_for_status()
                all_font_families.extend(
                    [item for item in response.json() if isinstance(item, dict) and item.get("type") == "dir"]
                )

            if not all_font_families:
                return []

            num_to_select = min(limit, len(all_font_families))
            selected_families = random.sample(all_font_families, k=num_to_select)

            font_urls = []
            font_extensions = (".ttf", ".otf")

            for family in selected_families:
                try:
                    family_response = requests.get(family["url"], timeout=10)
                    family_response.raise_for_status()
                    font_files_data = family_response.json()

                    if not isinstance(font_files_data, list):
                        continue

                    valid_font_files = [
                        font_file
                        for font_file in font_files_data
                        if isinstance(font_file, dict)
                        and font_file.get("type") == "file"
                        and font_file.get("name", "").lower().endswith(font_extensions)
                    ]

                    if valid_font_files:
                        chosen_font = random.choice(valid_font_files)
                        if chosen_font.get("download_url"):
                            font_urls.append(chosen_font["download_url"])
                except requests.RequestException:
                    continue
            return font_urls
        except requests.RequestException:
            return []

    def _ensure_local_fonts(self, urls: List[str]) -> List[str]:
        paths: List[str] = []
        for u in urls:
            try:
                name = os.path.basename(urllib.parse.urlparse(u).path)
                if not name:
                    continue
                local_path = os.path.join(self.font_cache_dir, name)
                if os.path.isfile(local_path) and os.path.getsize(local_path) > 1024:
                    paths.append(local_path)
                    continue
                try:
                    urllib.request.urlretrieve(u, local_path)
                    if os.path.isfile(local_path) and os.path.getsize(local_path) > 1024:
                        paths.append(local_path)
                except Exception:
                    continue
            except Exception:
                continue
        return paths

    def _get_font(self, font_size: int):
        if self.available_fonts:
            random_font_path = random.choice(self.available_fonts)
            try:
                return ImageFont.truetype(random_font_path, font_size)
            except IOError:
                pass
        
        try:
            return ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            return ImageFont.load_default()
