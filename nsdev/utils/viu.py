import asyncio
import os
import re
import shutil
from types import SimpleNamespace

import httpx
from yt_dlp import YoutubeDL

from .logger import LoggerHandler


class ViuDownloader:
    def __init__(self, cookies_file_path: str = "cookies.txt", download_path: str = "downloads"):
        self.log = LoggerHandler()
        self.download_path = download_path
        os.makedirs(self.download_path, exist_ok=True)

        if not os.path.exists(cookies_file_path):
            raise FileNotFoundError(f"File cookie Viu tidak ditemukan di: {cookies_file_path}")

        if not shutil.which("yt-dlp"):
            raise EnvironmentError("yt-dlp tidak ditemukan. Pastikan sudah terinstal dan ada di PATH.")
        
        if not shutil.which("ffmpeg"):
            raise EnvironmentError("ffmpeg tidak ditemukan. Pastikan sudah terinstal dan ada di PATH.")

        self.cookies_file_path = cookies_file_path

    async def _run_yt_dlp_download(self, url: str) -> dict:
        self.log.print(f"{self.log.CYAN}Memulai unduhan Viu dengan yt-dlp untuk URL: {url}")

        ydl_opts = {
            "outtmpl": os.path.join(self.download_path, "%(title)s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "cookiefile": self.cookies_file_path,
            "restrictfilenames": True,
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "geo_bypass": True,
            "geo_bypass_country": "ID",
        }
        
        def sync_ydl_download():
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                final_filename = ydl.prepare_filename(info)

                if not os.path.exists(final_filename):
                    base_name = os.path.splitext(os.path.basename(final_filename))[0]
                    found_files = [f for f in os.listdir(self.download_path) if f.startswith(base_name) and f.endswith(".mp4")]
                    if found_files:
                        final_filename = os.path.join(self.download_path, found_files[0])
                    else:
                        raise FileNotFoundError(f"Final file not found after download: {final_filename}")

                return {
                    "path": final_filename,
                    "title": info.get("title", os.path.basename(final_filename)),
                    "duration": info.get("duration"),
                    "thumbnail": info.get("thumbnail")
                }

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, sync_ydl_download)
        
        self.log.print(f"{self.log.GREEN}Unduhan Viu selesai: {result['path']}")
        return result

    async def download(self, url: str) -> str:
        if "viu.com" not in url:
            raise ValueError("URL yang diberikan bukan dari viu.com.")
        
        download_info = await self._run_yt_dlp_download(url)
        
        return download_info['path']
