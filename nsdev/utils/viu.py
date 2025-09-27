import asyncio
import http.cookiejar
import os
import re
import shutil
import time
from types import SimpleNamespace
from urllib.parse import urlencode

import httpx
import orjson

from .logger import LoggerHandler
from .viu_ckey import CKey


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
        
        self.cookies = {}
        for cookie in jar:
            self.cookies[cookie.name] = cookie.value
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        return httpx.AsyncClient(headers=headers, cookies=self.cookies, follow_redirects=True, timeout=30)

    async def _get_media_info(self, video_id: str, url: str) -> SimpleNamespace:
        self.log.print(f"{self.log.CYAN}Mengambil detail video untuk ID: {video_id}")
        
        tm = str(int(time.time()))
        guid = self.cookies.get('guid', 'default_guid')
        ckey = CKey().make(vid=video_id, tm=tm, app_ver='2.5.13', guid=guid, platform='4830201', url=url)

        params = {
            'charge': '0', 'otype': 'json', 'defnpayver': '0', 'spau': '1', 'spaudio': '1',
            'spwm': '1', 'sphls': '1', 'host': 'wetv.vip', 'refer': 'wetv.vip', 'ehost': url,
            'sphttps': '1', 'encryptVer': '8.1', 'cKey': ckey, 'clip': '4', 'guid': guid,
            'flowid': '4bc874cf11eac741b34fa6e4c62ca18e', 'platform': '4830201',
            'sdtfrom': '1002', 'appVer': '2.5.13', 'vid': video_id, 'defn': 'shd',
            'fhdswitch': '0', 'dtype': '3', 'spsrt': '2', 'tm': tm, 'lang_code': '8229847',
            'spcaptiontype': '1', 'spmasterm3u8': '2', 'country_code': '153514', 'drm': '40'
        }
        
        api_url = f"https://play.wetv.vip/getvinfo?{urlencode(params)}"
        
        res = await self.client.get(api_url)
        res.raise_for_status()
        data = res.json()

        if 'sfl' not in data or not data['sfl']['fi']:
            raise ValueError("Tidak dapat menemukan stream info (sfl). Konten mungkin memerlukan premium atau tidak tersedia.")
        
        stream_info = data['sfl']['fi'][0]
        m3u8_url = f"{data['vl']['vi'][0]['ul']['ui'][0]['url']}{stream_info['name']}?{stream_info['key']}"
        title = data['vl']['vi'][0]['ti']
        
        clean_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
        
        return SimpleNamespace(url=m3u8_url, title=clean_title)

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
        
        video_details = await self._get_media_info(video_id, url)
        
        final_path = await self._run_downloader(video_details.url, video_details.title)
        
        return final_path
