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

        self.client, self.auth_token = self._prepare_client_and_token(cookies_file_path)

    def _prepare_client_and_token(self, cookie_path: str):
        jar = http.cookiejar.MozillaCookieJar(cookie_path)
        jar.load(ignore_discard=True, ignore_expires=True)
        
        cookies = httpx.Cookies()
        token = None
        for cookie in jar:
            cookies.set(cookie.name, cookie.value, domain=cookie.domain)
            if cookie.name == 'token':
                token = cookie.value
        
        if not token:
            raise ValueError("Cookie 'token' tidak ditemukan di dalam file cookies. Pastikan Anda sudah login.")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Authorization": f"Bearer {token}"
        }
        client = httpx.AsyncClient(headers=headers, cookies=cookies, follow_redirects=True, timeout=30)
        return client, token

    async def _get_product_info_from_html(self, url: str) -> SimpleNamespace:
        self.log.print(f"{self.log.CYAN}Mengekstrak info dari halaman HTML: {url}")
        try:
            response = await self.client.get(url, headers={"Authorization": ""})
            response.raise_for_status()
            
            series_id_match = re.search(r'"series_id":\s*"(\d+)"', response.text)
            product_id_match = re.search(r'"product_id":\s*"(\d+)"', response.text)
            series_name_match = re.search(r'"series_name":\s*"(.*?)"', response.text)
            
            if not series_id_match or not product_id_match or not series_name_match:
                raise ValueError("Gagal mengekstrak series_id, product_id, atau series_name dari halaman HTML.")

            return SimpleNamespace(
                series_id=series_id_match.group(1),
                product_id=product_id_match.group(1),
                series_name=series_name_match.group(1)
            )
        except Exception as e:
            raise RuntimeError(f"Gagal mengambil atau mem-parsing halaman Viu: {e}")

    async def _get_ccs_product_id(self, series_id: str, target_product_id: str) -> str:
        self.log.print(f"{self.log.CYAN}Mencari CCS Product ID untuk Series ID: {series_id}")
        api_url = "https://api-gateway-global.viu.com/api/mobile"
        params = {
            "platform_flag_label": "web",
            "area_id": "1001",
            "language_flag_id": "3",
            "series_id": series_id,
            "size": "-1",
            "sort": "asc",
            "r": "/vod/product-list",
        }
        
        response = await self.client.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()

        product_list = data.get("data", {}).get("product_list", [])
        if not product_list:
            raise ValueError(f"Tidak ada daftar episode yang ditemukan untuk series_id {series_id}.")

        for product in product_list:
            if str(product.get("product_id")) == target_product_id:
                ccs_id = product.get("ccs_product_id")
                if ccs_id:
                    return ccs_id
        
        raise ValueError(f"CCS Product ID tidak ditemukan untuk product_id {target_product_id} di dalam series.")

    async def _get_m3u8_url(self, ccs_product_id: str) -> str:
        self.log.print(f"{self.log.CYAN}Mengambil manifest streaming untuk CCS ID: {ccs_product_id}")
        api_url = "https://api-gateway-global.viu.com/api/playback/distribute"
        params = {
            "platform_flag_label": "web",
            "area_id": "1001",
            "language_flag_id": "3",
            "ccs_product_id": ccs_product_id
        }

        response = await self.client.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()

        manifests = data.get("data", {}).get("stream", {}).get("url", {})
        
        for res in ["s1080p", "s720p", "s480p", "s240p"]:
            if manifests.get(res):
                self.log.print(f"{self.log.GREEN}Manifest ditemukan untuk resolusi: {res}")
                return manifests[res]

        raise ValueError("Tidak dapat menemukan URL M3U8 yang valid dalam respons API.")

    async def _run_downloader(self, m3u8_url: str, output_filename: str) -> str:
        clean_title = re.sub(r'[\\/*?:"<>|]', "", output_filename).strip()
        ffmpeg_path = shutil.which("ffmpeg")

        command = [
            "N_m3u8DL-RE", m3u8_url,
            "--save-name", clean_title,
            "--work-dir", self.download_path,
            "--binary-merge",
            "--use-ffmpeg-binary-path", ffmpeg_path,
            "--auto-select"
        ]
        
        self.log.print(f"{self.log.YELLOW}Memulai proses unduh dengan N_m3u8DL-RE...")
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_details = stderr.decode('utf-8', errors='ignore')
            self.log.print(f"{self.log.RED}Download gagal. Detail:\n{error_details}")
            raise RuntimeError(f"N_m3u8DL-RE gagal dengan kode {process.returncode}.")
        
        final_file_path = os.path.join(self.download_path, f"{clean_title}.mp4")
        if not os.path.exists(final_file_path):
             for ext in [".mkv", ".ts"]:
                 potential_file = os.path.join(self.download_path, f"{clean_title}{ext}")
                 if os.path.exists(potential_file):
                     final_file_path = potential_file
                     break
        
        if not os.path.exists(final_file_path):
            raise FileNotFoundError(f"File hasil unduhan tidak ditemukan setelah proses selesai.")

        self.log.print(f"{self.log.GREEN}Video berhasil diunduh ke: {final_file_path}")
        return final_file_path

    async def download(self, url: str) -> str:
        html_info = await self._get_product_info_from_html(url)
        
        ccs_product_id = await self._get_ccs_product_id(html_info.series_id, html_info.product_id)
        
        m3u8_url = await self._get_m3u8_url(ccs_product_id)
        
        final_path = await self._run_downloader(m3u8_url, html_info.series_name)
        
        return final_path
