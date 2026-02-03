import asyncio
import os
from functools import partial
from typing import List
from urllib.parse import urlparse

import wget
import yt_dlp

from ..data.ymlreder import YamlHandler

class MediaDownloader:
    def __init__(self, cookies_file_path: str = None, download_path: str = "downloads"):
        self.download_path = download_path
        self.cookies_file_path = cookies_file_path
        self.convert = YamlHandler()

        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

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
            "ignoreerrors": False,
            "socket_timeout": 60,
            "retries": 10,
            "fragment_retries": 10,
            "skip_unavailable_fragments": True,
            "restrictfilenames": True,
            "concurrent_fragment_downloads": 4
        }
        if self.cookies_file_path and os.path.exists(self.cookies_file_path):
            opts["cookiefile"] = self.cookies_file_path
        return opts

    def _sync_search_youtube(self, query: str, limit: int = 10):
        opts = self._base_opts()
        opts.update({
            "default_search": f"ytsearch{limit}",
            "format": "bv*+ba/best"
        })
        with yt_dlp.YoutubeDL(opts) as ydl:
            result = ydl.extract_info(query, download=False)
            if not result:
                return []
            entries = result.get("entries") or []
            if isinstance(entries, dict):
                entries = [entries]
            clean = []
            for item in entries:
                if item:
                    clean.append(self.convert._convertToNamespace(item))
            return clean

    async def search_youtube(self, query: str, limit: int = 10) -> List:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._sync_search_youtube, query, limit))

    def _sync_download(self, url: str, audio_only: bool, progress_callback, loop):
        opts = self._base_opts()
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
                "format": "bv*+ba/best",
                "merge_output_format": "mp4"
            })

        if progress_callback:
            def hook(d):
                if d.get("status") == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate")
                    if total:
                        asyncio.run_coroutine_threadsafe(
                            progress_callback(d["downloaded_bytes"], total),
                            loop
                        )
            opts["progress_hooks"] = [hook]

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise Exception("Media tidak dapat diambil")

            if "entries" in info and isinstance(info["entries"], list):
                info = next((x for x in info["entries"] if x), None)

            if not info:
                raise Exception("Tidak ada data valid")

            out_file = ydl.prepare_filename(info)
            ns = self.convert._convertToNamespace(info)

            base, ext = os.path.splitext(out_file)
            if audio_only:
                out_file = base + ".mp3"
            else:
                out_file = base + ".mp4"

            ns.downloaded_path = out_file

            thumb_url = getattr(ns, "thumbnail", None)
            thumb_path = None

            if not thumb_url and self._is_youtube(url) and hasattr(ns, "id"):
                thumb_url = f"https://i.ytimg.com/vi/{ns.id}/maxresdefault.jpg"

            if thumb_url:
                try:
                    thumb_path = wget.download(thumb_url, out=self.download_path)
                except:
                    thumb_path = None

            ns.thumbnail_path = thumb_path
            return ns

    async def download(self, url: str, audio_only: bool = False, progress_callback=None):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._sync_download, url, audio_only, progress_callback, loop))

    async def download_social(self, url: str, audio_only: bool = False, progress_callback=None):
        if self._is_instagram(url) or self._is_twitter(url) or self._is_tiktok(url):
            return await self.download(url, audio_only, progress_callback)
        raise Exception("URL tidak didukung")
