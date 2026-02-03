import asyncio
import os
from functools import partial
from typing import List
from urllib.parse import urlparse

import wget
import yt_dlp
from faker import Faker

from ..data.ymlreder import YamlHandler

class MediaDownloader:
    def __init__(self, cookies_file_path: str = None, download_path: str = "downloads"):
        self.download_path = download_path
        self.cookies_file_path = cookies_file_path
        self.fake = Faker("id_ID")
        self.convert = YamlHandler()

        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def _get_headers(self):
        return {
            "User-Agent": self.fake.user_agent(),
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _is_platform(self, url: str, domains: List[str]):
        parsed = urlparse(url)
        return any(parsed.netloc.lower().endswith(domain) for domain in domains)

    def _is_youtube(self, url: str):
        return self._is_platform(url, ["youtube.com", "youtu.be"])

    def _is_instagram(self, url: str):
        return self._is_platform(url, ["instagram.com", "instagr.am"])

    def _is_twitter(self, url: str):
        return self._is_platform(url, ["twitter.com", "x.com"])

    def _is_tiktok(self, url: str):
        return self._is_platform(url, ["tiktok.com", "vt.tiktok.com"])

    def _base_opts(self):
        opts = {
            "outtmpl": os.path.join(self.download_path, "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "socket_timeout": 30,
            "retries": 5,
            "http_headers": self._get_headers(),
            "restrictfilenames": True,
            "concurrent_fragment_downloads": 4,
        }
        if self.cookies_file_path and os.path.exists(self.cookies_file_path):
            opts["cookiefile"] = self.cookies_file_path
        return opts

    def _sync_search_youtube(self, query: str, limit: int = 10):
        opts = self._base_opts().copy()
        opts.update({
            "format": "best",
            "default_search": f"ytsearch{limit}",
            "noplaylist": True,
        })
        with yt_dlp.YoutubeDL(opts) as ydl:
            result = ydl.extract_info(query, download=False) or {}
            entries = result.get("entries", [])
            if not entries and "id" in result:
                entries = [result]
            return [self.convert._convertToNamespace(item) for item in entries]

    async def search_youtube(self, query: str, limit: int = 10) -> List:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._sync_search_youtube, query, limit))

    def _sync_download(self, url: str, audio_only: bool, progress_callback, loop, platform_name: str):
        opts = self._base_opts().copy()
        if audio_only:
            opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                }]
            })
        else:
            opts.update({
                "format": "best/bestvideo+bestaudio",
                "merge_output_format": "mp4",
            })

        if progress_callback:
            def hook(d):
                if d.get("status") == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate")
                    if total:
                        asyncio.run_coroutine_threadsafe(progress_callback(d["downloaded_bytes"], total), loop)
            opts["progress_hooks"] = [hook]

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            ns = self.convert._convertToNamespace(info)

            out_file = ydl.prepare_filename(info)
            if not audio_only and opts.get("merge_output_format") == "mp4":
                base, _ = os.path.splitext(out_file)
                out_file = base + ".mp4"
            if audio_only:
                base, _ = os.path.splitext(out_file)
                out_file = base + ".mp3"

            ns.downloaded_path = out_file

            thumb_path = None
            thumb_url = getattr(ns, "thumbnail", None)
            if not thumb_url and self._is_youtube(url) and hasattr(ns, "id"):
                thumb_url = f"https://i.ytimg.com/vi/{ns.id}/maxresdefault.jpg"
            if thumb_url:
                try:
                    thumb_path = wget.download(thumb_url, out=self.download_path)
                except Exception:
                    thumb_path = None

            ns.thumbnail_path = thumb_path
            return ns

    async def download(self, url: str, audio_only: bool = False, progress_callback=None):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._sync_download, url, audio_only, progress_callback, loop, "Media"))

    async def download_social(self, url: str, audio_only: bool = False, progress_callback=None):
        if self._is_instagram(url):
            return await self.download(url, audio_only, progress_callback)
        if self._is_twitter(url):
            return await self.download(url, audio_only, progress_callback)
        if self._is_tiktok(url):
            return await self.download(url, audio_only, progress_callback)
        raise Exception("Unsupported URL format")
