import asyncio
import json
import os
import re
from functools import partial
from typing import Dict, Optional, Tuple, Union

import fake_useragent
import httpx

from .logger import LoggerHandler


class PinterestDownloader:
    def __init__(self, cookies_file_path: Optional[str] = None, logging_enabled: bool = True):
        self.cookies = self._parse_cookie_file(cookies_file_path) if cookies_file_path else None
        self.base_url = "https://www.pinterest.com"
        self.client = httpx.AsyncClient(
            cookies=self.cookies,
            headers={
                "User-Agent": fake_useragent.UserAgent().random,
                "Accept-Language": "en-US,en;q=0.5",
            },
            follow_redirects=True,
            timeout=30,
        )
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()

    def _parse_cookie_file(self, file_path: str) -> Dict[str, str]:
        if not os.path.exists(file_path):
            self.__log(f"{self.log.YELLOW}Cookie file not found at {file_path}, proceeding without cookies.")
            return {}

        cookies_dict = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("#") or line.strip() == "":
                    continue
                parts = line.strip().split("\t")
                if len(parts) >= 7:
                    cookies_dict[parts[5]] = parts[6]
        return cookies_dict

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    async def _get_media_from_html(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        response = await self.client.get(url)
        response.raise_for_status()
        html_content = response.text

        json_data_match = re.search(r'<script id="initial-state" type="application/json">(.+?)</script>', html_content)
        if not json_data_match:
            raise ValueError("Could not find media data on the page.")

        data = json.loads(json_data_match.group(1))

        try:
            pin_data = next(
                res["response"]["data"]
                for res in data.get("resourceResponses", [])
                if res.get("name") == "PinResource"
            )

            if "videos" in pin_data and pin_data["videos"]:
                video_details = pin_data["videos"]["video_list"]
                best_quality_video = video_details.get("V_EXP7_HLS") or next(iter(video_details.values()), None)
                if best_quality_video:
                    return "video", best_quality_video["url"]

            if "images" in pin_data and pin_data["images"]:
                return "image", pin_data["images"]["orig"]["url"]

        except (KeyError, StopIteration):
            raise ValueError("Failed to parse media information from JSON data.")

        return None, None

    async def _download_content(self, url: str) -> bytes:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=60)
            response.raise_for_status()
            return response.content

    async def download(self, url: str) -> Dict[str, Union[str, bytes]]:
        if "pinterest.com/pin/" not in url:
            raise ValueError("Invalid Pinterest Pin URL provided.")

        self.__log(f"{self.log.GREEN}Fetching media from: {url}")
        media_type, media_url = await self._get_media_from_html(url)

        if not media_type or not media_url:
            raise ValueError("No downloadable media found for this Pin.")

        self.__log(f"{self.log.GREEN}Found {media_type}, downloading from: {media_url}")

        if media_type == "video" and media_url.endswith(".m3u8"):
            raise ValueError("HLS video streaming (.m3u8) is not directly downloadable with this method.")

        media_bytes = await self._download_content(media_url)
        self.__log(f"{self.log.GREEN}Download successful, size: {len(media_bytes) / 1024:.2f} KB")

        return {"media_type": media_type, "media_bytes": media_bytes, "source_url": media_url}
