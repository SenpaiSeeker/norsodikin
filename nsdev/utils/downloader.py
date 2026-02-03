import asyncio
import os
from functools import partial
from typing import List
from urllib.parse import urlparse

import wget
from faker import Faker
from yt_dlp import YoutubeDL

from ..data.ymlreder import YamlHandler


class MediaDownloader:
    def __init__(self, cookies_file_path: str = "cookies.txt", download_path: str = "downloads"):
        self.download_path = download_path
        self.cookies_file_path = cookies_file_path

        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        self.convert = YamlHandler()
        self.fake = Faker("id_ID")

    def _is_youtube_url(self, url):
        parsed_url = urlparse(url)
        return parsed_url.netloc in ("www.youtube.com", "youtube.com", "youtu.be")

    def _is_instagram_url(self, url):
        parsed_url = urlparse(url)
        return parsed_url.netloc in ("www.instagram.com", "instagram.com", "instagr.am")

    def _is_twitter_url(self, url):
        parsed_url = urlparse(url)
        return parsed_url.netloc in ("twitter.com", "www.twitter.com", "x.com", "www.x.com")

    def _is_tiktok_url(self, url):
        parsed_url = urlparse(url)
        return parsed_url.netloc in ("www.tiktok.com", "tiktok.com", "vt.tiktok.com")

    def _get_headers(self, url=None):
        headers = {
            "User-Agent": self.fake.user_agent(),
            "Accept-Language": "en-US,en;q=0.9",
        }

        if url and "cloud.hownetwork.xyz" in url:
            video_id = url.split("/")[-3]
            referer_url = f"https://cloud.hownetwork.xyz/video.php?id={video_id}"
            headers["Referer"] = referer_url

        elif url:
            headers["Referer"] = "https://www.google.com/"

        return headers

    def _sync_extract_info(self, query: str, limit: int = 10):
        ydl_opts = {
            "format": "best",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "extract_flat": "in_playlist",
            "nocheckcertificate": True,
            "geo_bypass": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "android", "web"],
                    "skip": ["webpage", "auth_check"],
                }
            },
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "http_headers": self._get_headers(query if query.startswith("http") else None),
        }

        is_url = query.startswith("http")
        if is_url:
            ydl_opts["noplaylist"] = False
        else:
            ydl_opts["default_search"] = f"ytsearch{limit}"

        with YoutubeDL(ydl_opts) as ydl:
            try:
                result = ydl.extract_info(query, download=False)
                if not result:
                    return []

                entries = result.get("entries", [])
                if not entries and "id" in result:
                    entries = [result]

                return [self.convert._convertToNamespace(entry) for entry in entries]
            except Exception as e:
                raise Exception(f"Gagal mencari video: {e}")

    async def search_youtube(self, query: str, limit: int = 10) -> List:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._sync_extract_info, query, limit))

    def _build_ydl_opts(self, url: str, audio_only: bool, progress_callback, loop, use_flexible_format: bool = False):
        def _hook(d):
            if d["status"] == "downloading" and progress_callback:
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate")
                if total_bytes:
                    asyncio.run_coroutine_threadsafe(progress_callback(d["downloaded_bytes"], total_bytes), loop)

        opts = {
            "outtmpl": os.path.join(self.download_path, "%(id)s.%(ext)s"),
            "no_warnings": True,
            "noplaylist": True,
            "quiet": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "ignoreerrors": True,
            "user_agent": self.fake.user_agent(),
            "http_headers": self._get_headers(url),
            "hls_prefer_native": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "android", "web"],
                    "skip": ["webpage", "auth_check"],
                }
            },
            "restrictfilenames": True,
            "concurrent_fragment_downloads": 4,
        }

        if self.cookies_file_path and os.path.exists(self.cookies_file_path):
            opts["cookiefile"] = self.cookies_file_path

        if progress_callback:
            opts["progress_hooks"] = [_hook]

        if audio_only:
            opts.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                }
            )
        else:
            if use_flexible_format:
                opts.update(
                    {
                        "format": "bestvideo+bestaudio/best",
                        "merge_output_format": "mp4",
                    }
                )
            else:
                opts.update(
                    {
                        "format": "bestvideo[ext=mp4][height<=?720][width<=?1280]+bestaudio[ext=m4a]/best",
                        "merge_output_format": "mp4",
                    }
                )
        return opts

    def _sync_download(self, url, audio_only, progress_callback, loop, use_flexible_format):
        ydl_opts = self._build_ydl_opts(url, audio_only, progress_callback, loop, use_flexible_format)
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                result_obj = self.convert._convertToNamespace(info)

                filename = ydl.prepare_filename(info)

                if not audio_only and ydl_opts.get("merge_output_format") == "mp4":
                    base, _ = os.path.splitext(filename)
                    filename = base + ".mp4"

                if audio_only and filename:
                    base, _ = os.path.splitext(filename)
                    filename = base + ".mp3"

                thumb_path = None
                if hasattr(result_obj, "id"):
                    try:
                        thumb_url = f"https://i.ytimg.com/vi/{result_obj.id}/maxresdefault.jpg"
                        thumb_path = wget.download(thumb_url, out=self.download_path)
                    except Exception:
                        thumb_path = None

                result_obj.downloaded_path = filename
                result_obj.thumbnail_path = thumb_path

                return result_obj
        except Exception as e:
            if "HTTP Error 403" in str(e):
                raise Exception("Akses ditolak (403). Server memblokir permintaan.")
            else:
                raise Exception(f"Gagal mengunduh: {e}")

    async def download(self, url: str, audio_only: bool = False, progress_callback: callable = None, use_flexible_format: bool = True) -> object:
        loop = asyncio.get_running_loop()
        func_call = partial(self._sync_download, url, audio_only, progress_callback, loop, use_flexible_format)
        return await loop.run_in_executor(None, func_call)

    def _sync_download_social(self, url, audio_only, progress_callback, loop, media_name):
        ydl_opts = self._build_ydl_opts(url, audio_only, progress_callback, loop, use_flexible_format=False)
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                result_obj = self.convert._convertToNamespace(info)

                filename = ydl.prepare_filename(info)

                if not audio_only and ydl_opts.get("merge_output_format") == "mp4":
                    base, _ = os.path.splitext(filename)
                    filename = base + ".mp4"

                if audio_only and filename:
                    base, _ = os.path.splitext(filename)
                    filename = base + ".mp3"

                thumb_path = None
                if hasattr(result_obj, "thumbnail") and result_obj.thumbnail:
                    try:
                        thumb_url = result_obj.thumbnail
                        thumb_path = wget.download(thumb_url, out=self.download_path)
                    except Exception:
                        thumb_path = None

                result_obj.downloaded_path = filename
                result_obj.thumbnail_path = thumb_path

                if not hasattr(result_obj, "title"):
                    result_obj.title = media_name

                return result_obj
        except Exception as e:
            if "HTTP Error 403" in str(e):
                raise Exception(f"❌ {media_name}: Akses ditolak (403).")
            else:
                raise Exception(f"❌ {media_name}: {e}")

    async def download_instagram(self, url, audio_only=False, progress_callback=None):
        loop = asyncio.get_running_loop()
        func_call = partial(self._sync_download_social, url, audio_only, progress_callback, loop, "Instagram Media")
        return await loop.run_in_executor(None, func_call)

    async def download_twitter(self, url, audio_only=False, progress_callback=None):
        loop = asyncio.get_running_loop()
        func_call = partial(self._sync_download_social, url, audio_only, progress_callback, loop, "Twitter Media")
        return await loop.run_in_executor(None, func_call)

    async def download_tiktok(self, url, audio_only=False, progress_callback=None):
        loop = asyncio.get_running_loop()
        func_call = partial(self._sync_download_social, url, audio_only, progress_callback, loop, "TikTok Media")
        return await loop.run_in_executor(None, func_call)

    async def download_social_media(self, url, audio_only=False, progress_callback=None):
        if self._is_instagram_url(url):
            return await self.download_instagram(url, audio_only, progress_callback)
        elif self._is_twitter_url(url):
            return await self.download_twitter(url, audio_only, progress_callback)
        elif self._is_tiktok_url(url):
            return await self.download_tiktok(url, audio_only, progress_callback)
        else:
            raise Exception("URL tidak didukung. Gunakan URL Instagram, Twitter/X, atau TikTok.")
