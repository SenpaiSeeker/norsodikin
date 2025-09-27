import asyncio
import http.cookiejar
import os
import re
import shutil
from types import SimpleNamespace

import httpx

from .logger import LoggerHandler


class ViuDownloader:
    def __init__(self, cookies_file_path: str = "cookies.txt", download_path: str = "downloads"):
        self.log = LoggerHandler()
        self.download_path = download_path
        os.makedirs(self.download_path, exist_ok=True)

        if not os.path.exists(cookies_file_path):
            raise FileNotFoundError(f"File cookie Viu tidak ditemukan di: {cookies_file_path}")

        if not shutil.which("N_m3u8DL-RE"):
            raise EnvironmentError("N_m3u8DL-RE tidak ditemukan. Pastikan sudah terinstal dan ada di PATH.")
        
        if not shutil.which("ffmpeg"):
            raise EnvironmentError("ffmpeg tidak ditemukan. Pastikan sudah terinstal dan ada di PATH.")

        self.client = self._prepare_client(cookies_file_path)

    def _prepare_client(self, cookie_path: str) -> httpx.AsyncClient:
        jar = http.cookiejar.MozillaCookieJar(cookie_path)
        jar.load(ignore_discard=True, ignore_expires=True)
        
        cookies = httpx.Cookies()
        for cookie in jar:
            cookies.set(cookie.name, cookie.value, domain=cookie.domain)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        return httpx.AsyncClient(headers=headers, cookies=cookies, follow_redirects=True, timeout=30)

    async def _get_m3u8_url(self, video_id: str) -> SimpleNamespace:
        self.log.print(f"{self.log.CYAN}Mengambil detail video untuk ID: {video_id}")
        api_url = f"https://www.viu.com/api/v2/play?ccs_product_id={video_id}"
        
        request_headers = self.client.headers.copy()
        request_headers['Referer'] = f"https://www.viu.com/ott/id/id/vod/{video_id}/"

        response = await self.client.get(api_url, headers=request_headers)
        
        if response.status_code == 404:
            raise ValueError("API mengembalikan 404 Not Found. ID video mungkin salah atau konten tidak tersedia.")
        
        response.raise_for_status()
        data = response.json()

        stream_data = data.get("data", {}).get("stream", {})
        hls_url = stream_data.get("hls", {}).get("url")
        title = data.get("data", {}).get("series", {}).get("name", f"viu_video_{video_id}")
        
        if not hls_url:
            raise ValueError("Tidak dapat menemukan URL M3U8 dalam respons API. Cookie mungkin tidak valid atau konten ini memerlukan premium.")
        
        clean_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
        
        return SimpleNamespace(url=hls_url, title=clean_title)

    async def _run_downloader(self, m3u8_url: str, output_filename: str) -> str:
        output_path = os.path.join(self.download_path, output_filename)
        ffmpeg_path = shutil.which("ffmpeg")

        command = (
            f'N_m3u8DL-RE "{m3u8_url}" '
            f'--save-name "{output_filename}" '
            f'--work-dir "{self.download_path}" '
            f'--binary-merge '
            f'--use-ffmpeg-binary-path "{ffmpeg_path}" '
            f'--auto-select'
        )
        
        self.log.print(f"{self.log.YELLOW}Memulai proses unduh dengan N_m3u8DL-RE...")
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_details = stderr.decode('utf-8', errors='ignore')
            self.log.print(f"{self.log.RED}Download gagal. Detail:\n{error_details}")
            raise RuntimeError(f"N_m3u8DL-RE gagal dengan kode {process.returncode}. Error: {error_details}")
        
        final_file_path = f"{output_path}.mp4"
        if not os.path.exists(final_file_path):
             all_files = os.listdir(self.download_path)
             for file in all_files:
                 if file.startswith(output_filename) and file.endswith((".mp4", ".mkv")):
                     final_file_path = os.path.join(self.download_path, file)
                     break

        self.log.print(f"{self.log.GREEN}Video berhasil diunduh ke: {final_file_path}")
        return final_file_path

    async def download(self, url: str) -> str:
        match = re.search(r"/vod/(\d+)/", url)
        if not match:
            raise ValueError("URL Viu tidak valid atau tidak mengandung ID video.")
        
        video_id = match.group(1)
        
        video_details = await self._get_m3u8_url(video_id)
        
        final_path = await self._run_downloader(video_details.url, video_details.title)
        
        return final_path
