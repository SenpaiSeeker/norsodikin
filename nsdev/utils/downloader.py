import asyncio
import os
import tempfile
from functools import partial
from types import SimpleNamespace
from typing import List
from urllib.parse import urlparse

import requests
from yt_dlp import YoutubeDL


class MediaDownloader:
    def __init__(self, cookies_file_path: str = "cookies.txt", download_path: str = "downloads"):
        self.download_path = download_path
        self.cookies_file_path = cookies_file_path
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def _is_youtube_url(self, url):
        parsed_url = urlparse(url)
        return parsed_url.netloc in ("www.youtube.com", "youtube.com", "youtu.be")

    def _sync_extract_info(self, query: str, limit: int = 10):
        ydl_opts = {
            "quiet": True,
            "noplaylist": True,
            "extract_flat": "in_playlist",
            "geo_bypass": True,
            "geo_bypass_country": "ID",
            "geo_verify": True
        }
        if self.cookies_file_path and os.path.exists(self.cookies_file_path):
            ydl_opts["cookiefile"] = self.cookies_file_path

        is_url = query.startswith("http")
        if is_url:
            ydl_opts["noplaylist"] = False
        else:
            ydl_opts["default_search"] = f"ytsearch{limit}"

        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(query, download=False)
            if not result:
                return []
            entries = result.get("entries", [])
            if not entries and "id" in result:
                entries = [result]
            return [
                SimpleNamespace(
                    id=entry.get("id"),
                    title=entry.get("title", "No Title"),
                    url=f"https://www.youtube.com/watch?v={entry.get('id')}",
                    duration=entry.get("duration", 0),
                    uploader=entry.get("uploader", "N/A")
                )
                for entry in entries
            ]

    async def search_youtube(self, query: str, limit: int = 10) -> List[SimpleNamespace]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._sync_extract_info, query, limit))

    def _sync_download(self, url: str, audio_only: bool, progress_callback: callable, loop: asyncio.AbstractEventLoop) -> dict:
        def _hook(d):
            if d["status"] == "downloading" and progress_callback:
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate")
                if total_bytes:
                    asyncio.run_coroutine_threadsafe(progress_callback(d["downloaded_bytes"], total_bytes), loop)

        output_template = os.path.join(self.download_path, "%(title)s.%(ext)s")
        temp_dir = tempfile.mkdtemp(prefix="yt_", dir=self.download_path)

        ydl_opts = {
            "outtmpl": output_template,
            "noplaylist": True,
            "quiet": True,
            "merge_output_format": "mp4",
            "geo_bypass": True,
            "geo_bypass_country": "ID",
            "geo_verify": True,
            "progress_hooks": [_hook],
            "retries": 10,
            "fragment_retries": 10,
            "continuedl": True,
            "concurrent_fragment_downloads": 3,
            "paths": {"home": temp_dir}
        }

        if self.cookies_file_path and os.path.exists(self.cookies_file_path):
            ydl_opts["cookiefile"] = self.cookies_file_path

        if audio_only:
            ydl_opts.update({
                "format": "bestaudio[ext=m4a]/bestaudio/best",
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
                ]
            })
        else:
            if self._is_youtube_url(url):
                ydl_opts["format"] = "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            else:
                ydl_opts["format"] = "best"

            ydl_opts["postprocessors"] = [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if audio_only:
                base, _ = os.path.splitext(filename)
                filename = base + ".mp3"

            if not os.path.exists(filename):
                alt_path = os.path.join(temp_dir, os.path.basename(filename))
                if os.path.exists(alt_path):
                    filename = alt_path

            thumbnail_path = None
            thumb_url = info.get("thumbnail")
            if thumb_url:
                try:
                    response = requests.get(thumb_url, timeout=10)
                    if response.ok:
                        thumb_file = os.path.join(self.download_path, f"{info.get('id')}.jpg")
                        with open(thumb_file, "wb") as f:
                            f.write(response.content)
                        thumbnail_path = thumb_file
                except Exception:
                    thumbnail_path = None

            return {
                "path": filename,
                "title": info.get("fulltitle", "N/A"),
                "duration": info.get("duration", 0),
                "thumbnail_path": thumbnail_path
            }

    async def download(self, url: str, audio_only: bool = False, progress_callback: callable = None) -> dict:
        loop = asyncio.get_running_loop()
        func_call = partial(self._sync_download, url, audio_only, progress_callback, loop)
        result = await loop.run_in_executor(None, func_call)
        return result
