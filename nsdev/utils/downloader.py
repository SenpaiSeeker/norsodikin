import asyncio
import os
from functools import partial
from typing import List, Optional
from urllib.parse import urlparse

import wget
from faker import Faker
from yt_dlp import YoutubeDL, utils as ytdl_utils

from ..data.ymlreder import YamlHandler
from .logger import LoggerHandler
from .vpn_manager import VPNManager


class MediaDownloader:
    def __init__(self, cookies_file_path: str = "cookies.txt", download_path: str = "downloads"):
        self.download_path = download_path
        self.cookies_file_path = cookies_file_path
        self.log = LoggerHandler()

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

    def _sync_extract_info(self, query: str, limit: int, ydl_opts: dict):
        is_url = query.startswith("http")
        if not is_url:
            ydl_opts["default_search"] = f"ytsearch{limit}"
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(query, download=False)
            if not result: return []
            entries = result.get("entries", [])
            if not entries and "id" in result: entries = [result]
            return [self.convert._convertToNamespace(entry) for entry in entries]
        except ytdl_utils.DownloadError as e:
            if "proxy" in ydl_opts and "Unable to connect to proxy" in str(e):
                self.log.print(f"{self.log.YELLOW}Pencarian via proxy gagal, mencoba koneksi langsung...{self.log.RESET}")
                del ydl_opts["proxy"]
                return self._sync_extract_info(query, limit, ydl_opts)
            raise Exception(f"Gagal mencari video: {e}")
        except Exception as e:
            raise Exception(f"Gagal mencari video: {e}")

    async def search_youtube(self, query: str, limit: int = 10, use_vpn_country: Optional[str] = None) -> List:
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
                self.log.print(f"{self.log.CYAN}Mencoba pencarian dengan proxy: {ydl_opts['proxy']}{self.log.RESET}")

        if self.cookies_file_path and os.path.exists(self.cookies_file_path):
            ydl_opts["cookiefile"] = self.cookies_file_path
            
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._sync_extract_info, query, limit, ydl_opts))

    async def _build_ydl_opts(self, progress_callback, loop, use_vpn_country: Optional[str] = None):
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
                
                self.log.print(f"{self.log.CYAN}Konfigurasi VPN dibuat: {filename}. Ini memerlukan setup OpenVPN di level sistem.{self.log.RESET}")
                
                best_server = await self.vpn_manager._get_best_vpn_server(country_code=use_vpn_country)
                if best_server:
                    opts['proxy'] = f"http://{best_server['IP']}:{best_server.get('port', '80')}"
                    self.log.print(f"{self.log.CYAN}Mencoba unduhan dengan proxy: {opts['proxy']}{self.log.RESET}")
            else:
                self.log.print(f"{self.log.YELLOW}Tidak dapat menemukan server VPN yang cocok untuk negara: {use_vpn_country}{self.log.RESET}")

        if progress_callback:
            opts["progress_hooks"] = [_hook]

        if self.cookies_file_path and os.path.exists(self.cookies_file_path):
            opts["cookiefile"] = self.cookies_file_path
        
        return opts

    def _sync_download(self, url: str, ydl_opts: dict):
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                result_obj = self.convert._convertToNamespace(info)

                filename = ydl.prepare_filename(info)

                is_audio = any(pp.get('key') == 'FFmpegExtractAudio' for pp in ydl_opts.get('postprocessors', []))

                if is_audio and filename:
                    base, _ = os.path.splitext(filename)
                    filename = base + ".mp3"

                thumb_path, thumb_url = None, None
                
                if hasattr(result_obj, 'thumbnail'): thumb_url = result_obj.thumbnail
                elif hasattr(result_obj, 'id'): thumb_url = f"https://i.ytimg.com/vi/{result_obj.id}/maxresdefault.jpg"

                if thumb_url:
                    try: thumb_path = wget.download(thumb_url, out=self.download_path)
                    except Exception: thumb_path = None

                result_obj.downloaded_path, result_obj.thumbnail_path = filename, thumb_path
                
                if not hasattr(result_obj, "title"): result_obj.title = "Downloaded Media"

                return result_obj
        except ytdl_utils.DownloadError as e:
            if "proxy" in ydl_opts and ("Unable to connect to proxy" in str(e) or "timed out" in str(e)):
                self.log.print(f"{self.log.YELLOW}Unduhan via proxy gagal, mencoba koneksi langsung...{self.log.RESET}")
                del ydl_opts["proxy"]
                return self._sync_download(url, ydl_opts)
            raise Exception(f"Gagal mengunduh: {e}")
        except Exception as e:
            raise Exception(f"Gagal mengunduh: {e}")

    async def download(self, url: str, audio_only: bool = False, progress_callback: callable = None, use_vpn_country: Optional[str] = None) -> object:
        loop = asyncio.get_running_loop()
        ydl_opts = await self._build_ydl_opts(progress_callback, loop, use_vpn_country)

        if audio_only:
            ydl_opts.update({"format": "bestaudio[ext=m4a]/bestaudio/best", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]})
        else:
            ydl_opts["format"] = "bestvideo[ext=mp4][height<=720][vcodec^=avc]+bestaudio/bestvideo[ext=mp4][height<=720]+bestaudio/best[ext=mp4][height<=720]/best"
        
        return await loop.run_in_executor(None, partial(self._sync_download, url, ydl_opts))

    async def download_social_media(self, url: str, audio_only: bool = False, progress_callback: callable = None, use_vpn_country: Optional[str] = None):
        loop = asyncio.get_running_loop()
        ydl_opts = await self._build_ydl_opts(progress_callback, loop, use_vpn_country)

        if audio_only:
            ydl_opts.update({"format": "bestaudio/best", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]})
        else:
            ydl_opts["format"] = "bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best"
            
        platform_name = "Social Media"
        if self._is_instagram_url(url): platform_name = "Instagram"
        elif self._is_twitter_url(url): platform_name = "Twitter/X"
        elif self._is_tiktok_url(url): platform_name = "TikTok"
        else: raise Exception("URL tidak didukung. Gunakan URL Instagram, Twitter/X, atau TikTok.")

        try:
            result = await loop.run_in_executor(None, partial(self._sync_download, url, ydl_opts))
            if not hasattr(result, "title") or not result.title:
                result.title = f"{platform_name} Media"
            return result
        except Exception as e:
            if "HTTP Error 403" in str(e):
                raise Exception(f"❌ {platform_name}: Akses ditolak (403). Gunakan cookies atau pastikan media publik.")
            else:
                raise Exception(f"❌ {platform_name}: {e}")
