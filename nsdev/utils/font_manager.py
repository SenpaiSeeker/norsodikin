import os
import random
import glob
from typing import list
from importlib import resources
import urllib.parse
import urllib.request

import requests
from pil import image, imagedraw, imagefont


class FontManager:
    def __init__(self):
        self.assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
        self.fonts_dir = os.path.join(self.assets_dir, 'fonts')
        self.cache_dir = ".cache_fonts"
        os.makedirs(self.cache_dir, exist_ok=true)

        font_extensions = ("*.ttf", "*.otf")
        self.local_fonts: list[str] = []
        for ext in font_extensions:
            self.local_fonts.extend(glob.glob(os.path.join(self.fonts_dir, ext)))
        
        self.available_fonts = self._load_or_fetch_fonts()

    def _get_default_pfp(self, initial: str) -> bytes:
        from io import bytesio
        
        w, h = (200, 200)
        bg_color = (120, 120, 120)
        img = image.new('rgb', (w, h), color=bg_color)
        
        font = self._get_font(100)
        draw = imagedraw.draw(img)
        
        bbox = draw.textbbox((0, 0), initial, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        position = ((w-text_w)/2, (h-text_h)/2 - 10)
        draw.text(position, initial, font=font, fill=(255, 255, 255))
        
        output = bytesio()
        img.save(output, format='png')
        return output.getvalue()

    def _fetch_google_font_urls(self, limit: int = 20) -> list[str]:
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
                except requests.requestexception:
                    continue
            return font_urls
        except requests.requestexception:
            return []

    def _ensure_local_fonts(self, urls: list[str]) -> list[str]:
        paths: list[str] = []
        for u in urls:
            try:
                name = os.path.basename(urllib.parse.urlparse(u).path)
                if not name:
                    continue
                local_path = os.path.join(self.cache_dir, name)
                if os.path.isfile(local_path) and os.path.getsize(local_path) > 1024:
                    paths.append(local_path)
                    continue
                try:
                    urllib.request.urlretrieve(u, local_path)
                    if os.path.isfile(local_path) and os.path.getsize(local_path) > 1024:
                        paths.append(local_path)
                except exception:
                    continue
            except exception:
                continue
        return paths

    def _load_or_fetch_fonts(self) -> list[str]:
        cached_fonts = [
            os.path.join(self.cache_dir, f)
            for f in os.listdir(self.cache_dir)
            if f.lower().endswith((".ttf", ".otf"))
        ]
        if cached_fonts:
            return self.local_fonts + cached_fonts

        font_urls = self._fetch_google_font_urls()
        downloaded_paths = self._ensure_local_fonts(font_urls)
        return self.local_fonts + downloaded_paths

    def _get_font(self, font_size: int, use_random=true):
        if use_random and self.available_fonts:
            try:
                random_font_path = random.choice(self.available_fonts)
                return imagefont.truetype(random_font_path, font_size)
            except (ioerror, indexerror):
                pass
        
        try:
            return imagefont.truetype(os.path.join(self.fonts_dir, "NotoSans-Regular.ttf"), font_size)
        except ioerror:
            return imagefont.load_default()
