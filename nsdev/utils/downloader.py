import asyncio
import os
from functools import partial
from typing import List
from urllib.parse import urlparse

import wget
from yt_dlp import YoutubeDL

from ..data.ymlreder import YamlHandler


class MediaDownloader:
    def __init__(self, cookies_file_path: str = "cookies.txt", download_path: str = "downloads"):
        self.download_path = download_path
        self.cookies_file_path = cookies_file_path

        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        self.convert = YamlHandler()

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

    def _get_headers(self, url: str =None):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
            "http_headers": self._get_headers(query),
        }
        
        if self.cookies_file_path and os.path.exists(self.cookies_file_path):
            ydl_opts["cookiefile"] = self.cookies_file_path

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
            "ignoreerrors": False,
            "source_address": "0.0.0.0",
            "http_headers": self._get_headers(url),
            "hls_prefer_native": True,
            "restrictfilenames": True,
            "concurrent_fragment_downloads": 4,
            "retries": 3,
            "fragment_retries": 3,
            "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
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

    def _normalize_info(self, info, error_message):
        if info is None:
            raise Exception(error_message)
        if "entries" in info:
            entries = [entry for entry in info.get("entries") or [] if entry]
            if not entries:
                raise Exception(error_message)
            info = entries[0]
        return info

    def _finalize_download_result(self, info, ydl, ydl_opts, audio_only, thumbnail_url):
        result_obj = self.convert._convertToNamespace(info)
        filename = ydl.prepare_filename(info)

        if not audio_only and ydl_opts.get("merge_output_format") == "mp4":
            base, _ = os.path.splitext(filename)
            filename = base + ".mp4"

        if audio_only and filename:
            base, _ = os.path.splitext(filename)
            filename = base + ".mp3"

        thumb_path = None
        if thumbnail_url:
            try:
                thumb_path = wget.download(thumbnail_url, out=self.download_path)
            except Exception:
                thumb_path = None

        result_obj.downloaded_path = filename
        result_obj.thumbnail_path = thumb_path

        return result_obj

    def _format_unavailable(self, error):
        return "Requested format is not available" in str(error)

    def _build_youtube_thumbnail(self, info):
        video_id = info.get("id") if isinstance(info, dict) else None
        if not video_id:
            return None
        return f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"

    def _attempt_download(self, url, audio_only, progress_callback, loop, use_flexible_format):
        ydl_opts = self._build_ydl_opts(url, audio_only, progress_callback, loop, use_flexible_format)
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            info = self._normalize_info(info, "Failed to extract video information.")
            thumb_url = self._build_youtube_thumbnail(info)
            return self._finalize_download_result(info, ydl, ydl_opts, audio_only, thumb_url)

    def _sync_download(self, url, audio_only, progress_callback, loop, use_flexible_format):
        try:
            return self._attempt_download(url, audio_only, progress_callback, loop, use_flexible_format)
        except Exception as e:
            if self._format_unavailable(e) and not use_flexible_format:
                return self._attempt_download(url, audio_only, progress_callback, loop, True)
            if "HTTP Error 403" in str(e):
                raise Exception("Akses ditolak (403). Server memblokir permintaan.")
            raise Exception(f"Gagal mengunduh: {e}")

    async def download(self, url: str, audio_only: bool = False, progress_callback: callable = None, use_flexible_format: bool = False) -> object:
        loop = asyncio.get_running_loop()
        func_call = partial(self._sync_download, url, audio_only, progress_callback, loop, use_flexible_format)
        return await loop.run_in_executor(None, func_call)

    def _build_social_thumbnail(self, info):
        if isinstance(info, dict):
            return info.get("thumbnail")
        return None

    def _attempt_download_social(self, url, audio_only, progress_callback, loop, media_name, use_flexible_format):
        ydl_opts = self._build_ydl_opts(url, audio_only, progress_callback, loop, use_flexible_format)
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            info = self._normalize_info(info, f"Failed to extract {media_name} information.")
            thumb_url = self._build_social_thumbnail(info)
            result_obj = self._finalize_download_result(info, ydl, ydl_opts, audio_only, thumb_url)
            if not hasattr(result_obj, "title"):
                result_obj.title = media_name
            return result_obj

    def _sync_download_social(self, url, audio_only, progress_callback, loop, media_name):
        try:
            return self._attempt_download_social(url, audio_only, progress_callback, loop, media_name, False)
        except Exception as e:
            if self._format_unavailable(e):
                return self._attempt_download_social(url, audio_only, progress_callback, loop, media_name, True)
            if "HTTP Error 403" in str(e):
                raise Exception(f"❌ {media_name}: Akses ditolak (403).")
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
