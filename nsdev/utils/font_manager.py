import os
import random
import urllib.parse
import urllib.request
from typing import List

import requests
from PIL import ImageFont


class FontManager:
    def __init__(self):
        self.font_cache_dir = ".cache_fonts"
        os.makedirs(self.font_cache_dir, exist_ok=True)
        self.available_fonts = self._load_or_fetch_fonts()

    def _load_or_fetch_fonts(self) -> List[str]:
        try:
            local_fonts = [
                os.path.join(self.font_cache_dir, f)
                for f in os.listdir(self.font_cache_dir)
                if f.lower().endswith((".ttf", ".otf")) and os.path.isfile(os.path.join(self.font_cache_dir, f))
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
        if self.available_fonts:
            random_font_path = random.choice(self.available_fonts)
            try:
                return ImageFont.truetype(random_font_path, font_size)
            except IOError:
                pass
        return ImageFont.load_default()
