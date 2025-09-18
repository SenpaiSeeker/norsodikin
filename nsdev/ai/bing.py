import asyncio
import os
import re
import time
from urllib.parse import urlencode, unquote

import httpx
import fake_useragent

from ..utils.logger import LoggerHandler


class ImageGenerator:
    def __init__(self, cookies_file_path: str = "cookies/Bing.txt", logging_enabled: bool = True):
        self.all_cookies = self._parse_cookie_file(cookies_file_path)
        self.auth_cookie = self.all_cookies.get("_U")

        if not self.auth_cookie:
            raise ValueError("File cookie harus berisi cookie '_U'.")

        self.base_url = "https://www.bing.com"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            cookies=self.all_cookies,
            headers={
                "User-Agent": fake_useragent.UserAgent().random,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://www.bing.com/images/create/",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
            },
            follow_redirects=True,
            timeout=200,
        )
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()

    def _parse_cookie_file(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File cookie tidak ditemukan: {file_path}")
        
        cookies = {}
        with open(file_path, 'r') as fp:
            for line in fp:
                if line.startswith('#') or not line.strip():
                    continue
                
                parts = line.strip().split('\t')
                if len(parts) >= 7:
                    if ".bing.com" in parts[0]:
                        cookies[parts[5]] = parts[6]
        return cookies

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)
    
    async def _poll_for_images(self, polling_url: str):
        start_time = time.time()
        self.__log(f"{self.log.CYAN}Meminta hasil gambar dari server...")

        while time.time() - start_time < 300:
            response = await self.client.get(polling_url)
            
            if response.status_code != 200:
                await asyncio.sleep(5)
                continue
            
            content = response.text
            if "errorMessage" in content or "blocked" in content.lower():
                raise Exception("Prompt Anda diblokir oleh kebijakan konten Bing.")
            
            image_urls = re.findall(r'src="([^"]+)"', content)
            
            valid_images = [
                unquote(url.split("?")[0]) for url in image_urls
                if "th.bing.com" in url and "r.bing.com" not in url
            ]

            if valid_images:
                self.__log(f"{self.log.GREEN}Berhasil menemukan {len(valid_images)} gambar.")
                return list(set(valid_images))
            
            await asyncio.sleep(5)
            
        raise Exception("Waktu tunggu habis saat mengambil gambar.")
        
    async def generate(self, prompt: str):
        self.__log(f"{self.log.GREEN}Memulai pembuatan gambar untuk prompt: '{prompt}'")
        
        encoded_prompt = urlencode({"q": prompt})
        request_url = f"/images/create?{encoded_prompt}&rt=4&FORM=GENCRE"

        self.__log(f"{self.log.CYAN}Mengirim permintaan pembuatan...")
        response = await self.client.get(request_url)
        
        if response.status_code != 200:
            raise Exception(f"Permintaan gagal, status: {response.status_code}. Periksa cookie.")
        
        if "interrupted" in str(response.url).lower():
            raise Exception("Otentikasi cookie gagal, permintaan diinterupsi.")
            
        polling_url = str(response.url)
        
        image_links = await self._poll_for_images(polling_url)
        return image_links
