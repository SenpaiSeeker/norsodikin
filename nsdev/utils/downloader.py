import asyncio
import os
from functools import partial
from typing import List, Optional
from urllib.parse import urlparse

import wget
from faker import Faker
from yt_dlp import YoutubeDL

from ..data.ymlreder import YamlHandler
from .vpn_manager import VPNManager


class MediaDownloader:
    def __init__(self, cookies_file_path: str = "cookies.txt", download_path: str = "downloads"):
        self.download_path = download_path
        self.cookies_file_path = cookies_file_path

        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        self.convert = YamlHandler()
        self.fake = Faker("id_ID")
        self.vpn_manager = VPNManager()

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

    async def _sync_extract_info(self, query: str, limit: int = 10, use_vpn_country: Optional[str] = None):
        ydl_opts = {
            "format": "best",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "extract_flat": "in_playlist",
            "user_agent": self.fake.user_agent(),
        }

        if use_vpn_country:
            best_server = await self.vpn_manager._get_best_vpn_server(country_code=use_vpn_country)
            if best_server:
                ydl_opts['proxy'] = f"http://{best_server['IP']}:{best_server.get('port', '80')}"

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

    async def search_youtube(self, query: str, limit: int = 10, use_vpn_country: Optional[str] = None) -> List:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._sync_extract_info, query, limit, use_vpn_country))

    async def _build_ydl_opts(self, url: str, audio_only: bool, progress_callback, loop, use_vpn_country: Optional[str] = None):
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
            "user_agent": self.fake.user_agent(),
        }
        
        if use_vpn_country:
            ovpn_config_tuple = await self.vpn_manager.get_ovpn_config(country_code=use_vpn_country)
            if ovpn_config_tuple:
                filename, config_data = ovpn_config_tuple
                ovpn_path = os.path.join(self.download_path, filename)
                with open(ovpn_path, 'w') as f:
                    f.write(config_data)
                
                print(f"Menggunakan konfigurasi VPN: {filename}. Ini memerlukan setup OpenVPN di level sistem. Yt-dlp akan mencoba direct connection.")
            else:
                print(f"Tidak dapat menemukan server VPN yang cocok untuk negara: {use_vpn_country}")


        if progress_callback:
            opts["progress_hooks"] = [_hook]

        if self.cookies_file_path and os.path.exists(self.cookies_file_path):
            opts["cookiefile"] = self.cookies_file_path

        if audio_only:
            opts.update(
                {
                    "format": "bestaudio[ext=m4a]/bestaudio/best",
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
            opts["format"] = (
                "bestvideo[ext=mp4][height<=720][vcodec^=avc]+bestaudio/bestvideo[ext=mp4][height<=720]+bestaudio/best[ext=mp4][height<=720]/best"
            )

        return opts

    async def _sync_download(self, url, audio_only, progress_callback, loop, use_vpn_country):
        ydl_opts = await self._build_ydl_opts(url, audio_only, progress_callback, loop, use_vpn_country)
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                result_obj = self.convert._convertToNamespace(info)

                filename = ydl.prepare_filename(info)

                if audio_only and filename:
                    base, _ = os.path.splitext(filename)
                    filename = base + ".mp3"

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
                raise Exception("Akses ditolak (403). " "Perbarui cookies.txt atau pastikan video publik.")
            else:
                raise Exception(f"Gagal mengunduh: {e}")

    async def download(self, url: str, audio_only: bool = False, progress_callback: callable = None, use_vpn_country: Optional[str] = None) -> object:
        loop = asyncio.get_running_loop()
        func_call = partial(self._sync_download, url, audio_only, progress_callback, loop, use_vpn_country)
        return await loop.run_in_executor(None, func_call)

    async def _sync_download_social(self, url, audio_only, progress_callback, loop, media_name, use_vpn_country):
        ydl_opts = await self._build_ydl_opts(url, audio_only, progress_callback, loop, use_vpn_country)
        ydl_opts["format"] = "best[ext=mp4]/best"
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                result_obj = self.convert._convertToNamespace(info)

                filename = ydl.prepare_filename(info)
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
                raise Exception(f"❌ {media_name}: Akses ditolak (403). Gunakan cookies atau pastikan media publik.")
            else:
                raise Exception(f"❌ {media_name}: {e}")

    async def download_instagram(self, url, audio_only=False, progress_callback=None, use_vpn_country=None):
        loop = asyncio.get_running_loop()
        func_call = partial(self._sync_download_social, url, audio_only, progress_callback, loop, "Instagram Media", use_vpn_country)
        return await loop.run_in_executor(None, func_call)

    async def download_twitter(self, url, audio_only=False, progress_callback=None, use_vpn_country=None):
        loop = asyncio.get_running_loop()
        func_call = partial(self._sync_download_social, url, audio_only, progress_callback, loop, "Twitter Media", use_vpn_country)
        return await loop.run_in_executor(None, func_call)

    async def download_tiktok(self, url, audio_only=False, progress_callback=None, use_vpn_country=None):
        loop = asyncio.get_running_loop()
        func_call = partial(self._sync_download_social, url, audio_only, progress_callback, loop, "TikTok Media", use_vpn_country)
        return await loop.run_in_executor(None, func_call)

    async def download_social_media(self, url, audio_only=False, progress_callback=None, use_vpn_country=None):
        if self._is_instagram_url(url):
            return await self.download_instagram(url, audio_only, progress_callback, use_vpn_country)
        elif self._is_twitter_url(url):
            return await self.download_twitter(url, audio_only, progress_callback, use_vpn_country)
        elif self._is_tiktok_url(url):
            return await self.download_tiktok(url, audio_only, progress_callback, use_vpn_country)
        else:
            raise Exception("URL tidak didukung. Gunakan URL Instagram, Twitter/X, atau TikTok.")
