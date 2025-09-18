import asyncio
import os
import re
import time
from urllib.parse import urlencode

import httpx
import fake_useragent

from ..utils.logger import LoggerHandler

class ImageGenerator:
    def __init__(self, cookies_file_path: str = "cookies.txt", logging_enabled: bool = True):
        self.session_id = None
        self.base_url = "https://www.bing.com"
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()
        
        self.cookie_string = self._parse_netscape_to_dict(cookies_file_path)
        self.client = self._prepare_client()

    def _parse_netscape_to_dict(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File cookie tidak ditemukan: {file_path}")
        
        cookies = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.strip().startswith('#'):
                    parts = line.strip().split('\t')
                    if len(parts) >= 7 and ".bing.com" in parts[0]:
                        cookies[parts[5]] = parts[6]
        return cookies

    def _prepare_client(self):
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "max-age=0",
            "content-type": "application/x-www-form-urlencoded",
            "referrer": f"{self.base_url}/images/create/",
            "origin": self.base_url,
            "user-agent": fake_useragent.UserAgent().random,
            "cookie": self.cookie_string
        }
        
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            follow_redirects=False,
            timeout=200,
        )

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)
    
    async def generate(self, prompt: str):
        self.__log(f"{self.log.GREEN}Memulai pembuatan gambar untuk prompt: '{prompt}'")
        
        encoded_prompt = urlencode({"q": prompt})
        url_create = f"/images/create?{encoded_prompt}&rt=4&FORM=GENCRE"

        self.__log(f"{self.log.CYAN}Mengirim permintaan pembuatan...")
        
        response = await self.client.post(url_create, follow_redirects=False)

        if response.status_code != 302:
            if response.status_code == 429:
                raise Exception("Terlalu banyak permintaan. Coba lagi nanti.")
            raise Exception("Permintaan gagal. Pastikan cookie Anda valid.")
        
        redirect_url = response.headers.get("Location", "")
        if "rd=1&rt=4" not in redirect_url:
            raise Exception(f"Redirect URL tidak valid. Respon diterima: {redirect_url}")
            
        final_redirect = await self.client.get(redirect_url, follow_redirects=False)
        result_url_path = final_redirect.headers.get("Location")
        if not result_url_path or not result_url_path.startswith("/images/create/async/results/"):
            raise Exception("Gagal mendapatkan result ID. Mungkin prompt diblokir oleh kebijakan konten.")

        result_id = result_url_path.split("/")[-1].split("?")[0]
        self.__log(f"{self.log.GREEN}Permintaan berhasil diterima. Result ID: {result_id}")
        
        polling_url = f"{self.base_url}{result_url_path}"

        start_time = time.time()
        while time.time() - start_time < 180:
            self.__log(f"{self.log.YELLOW}Memeriksa status generasi... ({int(time.time() - start_time)}s)")
            
            poll_response = await self.client.get(polling_url)
            if poll_response.status_code != 200:
                await asyncio.sleep(5)
                continue

            content_text = poll_response.text
            if "errorMessage" in content_text:
                raise Exception(f"Bing mengembalikan error: {content_text}")

            if "Od9u" in content_text or "Y6My" in content_text:
                await asyncio.sleep(5)
                continue

            image_urls_raw = re.findall(r'src="([^"]+)"', content_text)
            
            valid_image_urls = [
                url.split("?")[0]
                for url in image_urls_raw
                if "th.bing.com" in url
            ]

            if valid_image_urls:
                self.__log(f"{self.log.GREEN}Ditemukan {len(valid_image_urls)} gambar final.")
                return valid_image_urls
            else:
                 await asyncio.sleep(5)

        raise Exception("Waktu tunggu habis saat menghasilkan gambar.")
