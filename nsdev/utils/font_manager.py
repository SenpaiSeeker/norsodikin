import os
import random
import urllib.parse
import urllib.request
from typing import List

import requests

from importlib import resources
from PIL import ImageFont


class FontManager:
    def __init__(self):
        self.font_cache_dir = ".cache_fonts"
        os.makedirs(self.font_cache_dir, exist_ok=True)
        self.available_fonts = self._load_or_fetch_fonts()

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

    def _fetch_google_font_urls(self, limit: int = 100) -> List[str]:
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
        return ImageFont.load_default()

    def _get_font_from_package(self, font_filename, size):
        try:
            font_resource = resources.files('assets').joinpath('fonts', font_filename)
            with resources.as_file(font_resource) as font_path:
                return ImageFont.truetype(str(font_path), size)
        except (IOError, FileNotFoundError):
            return ImageFont.load_default()
