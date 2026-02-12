import asyncio
import os
import re
from functools import partial
from typing import List, Optional
from urllib.parse import urlparse

import wget
from faker import Faker
from yt_dlp import YoutubeDL

from ..data.ymlreder import YamlHandler


class MediaDownloader:
    def __init__(
        self,
        cookies_file_path: str = "cookies.txt",
        download_path: str = "downloads",
        proxy: Optional[str] = None,
        speed_limit: Optional[int] = None,
        max_parallel: int = 3,
    ):
        self.download_path = download_path
        self.cookies_file_path = cookies_file_path
        self.proxy = proxy
        self.speed_limit = speed_limit
        self.semaphore = asyncio.Semaphore(max_parallel)

        os.makedirs(self.download_path, exist_ok=True)

        self.convert = YamlHandler()
        self.fake = Faker("id_ID")

    def _sanitize_filename(self, name: str) -> str:
        name = re.sub(r'[\\/*?:"<>|]', "", name)
        return name.strip()

    def _is_supported_social(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return domain in (
            "www.instagram.com",
            "instagram.com",
            "instagr.am",
            "twitter.com",
            "www.twitter.com",
            "x.com",
            "www.x.com",
            "www.tiktok.com",
            "tiktok.com",
            "vt.tiktok.com",
        )

    def _is_youtube_url(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return domain in (
            "www.youtube.com",
            "youtube.com",
            "youtu.be",
            "m.youtube.com",
        )

    def _build_base_opts(self, progress_callback, loop):
        def _hook(d):
            if d["status"] == "downloading" and progress_callback:
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                if total:
                    asyncio.run_coroutine_threadsafe(
                        progress_callback(d["downloaded_bytes"], total),
                        loop,
                    )

        opts = {
            "outtmpl": os.path.join(
                self.download_path,
                "%(title).50s_%(id)s.%(ext)s",
            ),
            "restrictfilenames": True,
            "quiet": True,
            "no_warnings": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "noplaylist": True,
            "continuedl": True,
            "merge_output_format": "mkv",
            "user_agent": self.fake.user_agent(),
            "js_runtimes": {
                "node": {},
            },
            "remote_components": ["ejs:github"],
            "extractor_args": {
                "youtube": {
                    "player_client": ["web"],
                }
            },
        }

        if os.path.exists(self.cookies_file_path):
            opts["cookiefile"] = self.cookies_file_path

        if self.proxy:
            opts["proxy"] = self.proxy

        if self.speed_limit:
            opts["ratelimit"] = self.speed_limit

        if progress_callback:
            opts["progress_hooks"] = [_hook]

        return opts

    def _select_format(self, resolution: Optional[str], audio_only: bool):
        if audio_only:
            return "bestaudio/best"

        if resolution:
            return f"bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]"

        return "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]"

    def _sync_download(
        self,
        url: str,
        resolution: Optional[str],
        audio_only: bool,
        progress_callback,
        loop,
    ):
        opts = self._build_base_opts(progress_callback, loop)
        opts["format"] = self._select_format(resolution, audio_only)

        if audio_only:
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)

            filepath = ydl.prepare_filename(info)
            if audio_only:
                filepath = os.path.splitext(filepath)[0] + ".mp3"

            thumb_path = None
            thumb_url = info.get("thumbnail")

            if thumb_url:
                try:
                    safe_name = self._sanitize_filename(info.get("id", "thumb"))
                    thumb_file = os.path.join(self.download_path, f"{safe_name}_thumb.jpg")
                    wget.download(thumb_url, thumb_file)
                    thumb_path = thumb_file
                except Exception:
                    thumb_path = None

            result_obj = self.convert._convertToNamespace(info)
            result_obj.downloaded_path = filepath
            result_obj.thumbnail_path = thumb_path

            return result_obj

    async def download(
        self,
        url: str,
        resolution: Optional[str] = None,
        audio_only: bool = False,
        progress_callback=None,
    ):
        async with self.semaphore:
            loop = asyncio.get_running_loop()
            func = partial(
                self._sync_download,
                url,
                resolution,
                audio_only,
                progress_callback,
                loop,
            )
            return await loop.run_in_executor(None, func)

    async def download_batch(
        self,
        urls: List[str],
        resolution: Optional[str] = None,
        audio_only: bool = False,
    ):
        tasks = [
            self.download(url, resolution, audio_only)
            for url in urls
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def download_social(
        self,
        url: str,
        resolution: Optional[str] = None,
        audio_only: bool = False,
        progress_callback=None,
    ):
        if not self._is_supported_social(url):
            raise Exception("URL tidak didukung untuk social media")

        return await self.download(
            url,
            resolution=resolution,
            audio_only=audio_only,
            progress_callback=progress_callback,
        )

    async def search_youtube(self, query: str, limit: int = 10):
        loop = asyncio.get_running_loop()

        def _search():
            opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "user_agent": self.fake.user_agent(),
            }
            if self.cookies_file_path and os.path.exists(self.cookies_file_path):
                opts["cookiefile"] = self.cookies_file_path
            
            is_youtube_url = self._is_youtube_url(query)            
            if not is_youtube_url:
                opts.update(
                    {
                        "extract_flat": "in_playlist",
                        "ignoreerrors": True,
                        "default_search": f"ytsearch{limit}"
                    }
                )
            else:
                opts["extract_flat"] = False 

            with YoutubeDL(opts) as ydl:
                result = ydl.extract_info(query, download=False)
                entries = result.get("entries", [])
                
                if entries:
                    return [self.convert._convertToNamespace(e) for e in entries] 
                else: 
                    return [self.convert._convertToNamespace(result)]                

        return await loop.run_in_executor(None, _search)
