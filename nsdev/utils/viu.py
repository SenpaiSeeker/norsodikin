import asyncio
import http.cookiejar
import os
import re
import shutil
import time
from types import SimpleNamespace
from urllib.parse import urlencode

import httpx
import m3u8

from .logger import LoggerHandler
from .viu_ckey import ViuCKey


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
        self.jar = http.cookiejar.MozillaCookieJar(cookie_path)
        self.jar.load(ignore_discard=True, ignore_expires=True)
        
        cookies = httpx.Cookies()
        for cookie in self.jar:
            cookies.set(cookie.name, cookie.value, domain=cookie.domain)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        return httpx.AsyncClient(headers=headers, cookies=cookies, follow_redirects=True, timeout=30)

    async def _get_vid_and_title(self, url: str) -> SimpleNamespace:
        self.log.print(f"{self.log.CYAN}Mengambil VID dan judul dari: {url}")
        response = await self.client.get(url)
        response.raise_for_status()
        
        match = re.search(r'window\.__NUXT__=(\(function\(\)\{var a=(.+?);return a\}\)\(\));', response.text)
        if not match:
            raise ValueError("Tidak dapat menemukan data NUXT di halaman Viu. Strukturnya mungkin telah berubah.")
            
        data = orjson.loads(match.group(2))
        
        video_info = data.get('state', {}).get('vod', {}).get('first-product-detail', {}).get('data', {})
        if not video_info:
            raise ValueError("Tidak dapat menemukan detail produk di data halaman.")

        vid = video_info.get('current_product', {}).get('vid')
        title = video_info.get('series', {}).get('name', f"viu_video_{vid}")
        
        if not vid:
            raise ValueError("VID tidak ditemukan di data halaman.")
            
        clean_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
        
        return SimpleNamespace(vid=vid, title=clean_title)

    async def _get_m3u8_url(self, vid: str, title: str, page_url: str) -> SimpleNamespace:
        self.log.print(f"{self.log.CYAN}Mengambil URL M3U8 untuk VID: {vid}")
        
        guid = next((cookie.value for cookie in self.jar if cookie.name == '_ottUID'), None)
        if not guid:
            raise ValueError("Cookie '_ottUID' (guid) tidak ditemukan. Pastikan cookie valid.")

        tm = str(int(time.time()))
        ckey = ViuCKey().make(vid=vid, tm=tm, app_ver='2.5.13', guid=guid, platform='4830201', url=page_url)

        params = {
            'charge': '0', 'otype': 'json', 'defnpayver': '0', 'spau': '1', 'spaudio': '1',
            'spwm': '1', 'sphls': '1', 'host': 'www.viu.com', 'refer': 'www.viu.com',
            'ehost': page_url, 'sphttps': '1', 'encryptVer': '8.1', 'cKey': ckey,
            'clip': '4', 'guid': guid, 'platform': '4830201', 'sdtfrom': '1002',
            'appVer': '2.5.13', 'vid': vid, 'defn': 'shd', 'fhdswitch': '0', 'dtype': '3',
            'spsrt': '2', 'tm': tm, 'drm': '40',
            'callback': f'getinfo_callback_{int(time.time() * 1000)}'
        }
        
        getvinfo_url = f"https://api-gateway-global.viu.com/api/playback/getvinfo?{urlencode(params)}"
        
        response = await self.client.get(getvinfo_url)
        response.raise_for_status()
        
        json_text = re.search(r'getinfo_callback_\d+\((.*)\)', response.text).group(1)
        data = orjson.loads(json_text)
        
        if data.get("msg") == "fail":
            raise ValueError(f"API getvinfo gagal: {data.get('message', 'Error tidak diketahui')}")

        hls_info = data.get('vl', {}).get('vi', [{}])[0].get('ul', {}).get('hls', {})
        if not hls_info:
            raise ValueError("URL HLS tidak ditemukan dalam respons API.")

        m3u8_url = list(hls_info.values())[0]
        
        return SimpleNamespace(url=m3u8_url, title=title)

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
        page_info = await self._get_vid_and_title(url)
        video_details = await self._get_m3u8_url(page_info.vid, page_info.title, url)
        final_path = await self._run_downloader(video_details.url, video_details.title)
        return final_path
