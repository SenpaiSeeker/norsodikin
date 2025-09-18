import asyncio
import os
import re
import time
from urllib.parse import urlencode, urlparse

import httpx
import fake_useragent

from ..utils.logger import LoggerHandler

class ImageGenerator:
    def __init__(self, cookies_file_path: str = "cookies.txt", logging_enabled: bool = True):
        self.all_cookies = self._parse_netscape_cookie_file(cookies_file_path)
        
        required_cookies = ['_U', 'MUID', 'SRCHHPGUSR', 'SRCHUID', 'SRCHUSR']
        if not all(k in self.all_cookies for k in required_cookies):
            raise ValueError(f"Satu atau lebih cookie penting tidak ditemukan di file. Butuh: {', '.join(required_cookies)}")

        self.base_url = "https://www.bing.com"
        self.client = self._prepare_client()
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()

    def _prepare_client(self):
        cookie_jar = httpx.Cookies()
        for name, value in self.all_cookies.items():
            cookie_jar.set(name, value, domain=".bing.com")

        headers = {
            'User-Agent': fake_useragent.UserAgent().random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f"{self.base_url}/images/create",
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Upgrade-Insecure-Requests': '1',
        }
        
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            cookies=cookie_jar,
            follow_redirects=True,
            timeout=200,
        )

    def _parse_netscape_cookie_file(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File cookie tidak ditemukan: {file_path}")

        cookies_dict = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.strip().startswith("#"):
                    parts = line.strip().split('\t')
                    if len(parts) >= 7 and ".bing.com" in parts[0]:
                        cookies_dict[parts[5]] = parts[6]
        return cookies_dict

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    async def _poll_for_images(self, polling_url: str):
        start_time = time.time()
        self.__log(f"{self.log.YELLOW}Memulai polling untuk hasil gambar...")
        while time.time() - start_time < 180:
            response = await self.client.get(polling_url)
            response.raise_for_status()
            
            if response.status_code == 200:
                if "class=\"gil_err_msg\"" in response.text:
                    raise Exception("Pembuatan gambar gagal karena alasan kebijakan konten atau error dari Bing.")
                
                image_urls = re.findall(r'src="([^"]+)"', response.text)
                processed_urls = [url.split('?')[0] for url in image_urls if 'th.bing.com' in url and '?' in url]
                
                if len(processed_urls) >= 4:
                    return list(dict.fromkeys(processed_urls))
            
            await asyncio.sleep(5)
        raise TimeoutError("Waktu tunggu untuk pembuatan gambar habis.")

    async def generate(self, prompt: str):
        self.__log(f"{self.log.GREEN}Memulai pembuatan gambar untuk prompt: '{prompt}'")

        await self.client.get("/images/create")
        
        params = {'q': prompt, 'rt': '4', 'FORM': 'GENCRE'}
        encoded_params = urlencode(params)
        initiation_url = f'/images/create?{encoded_params}'
        
        self.__log(f"{self.log.CYAN}Mengirim permintaan awal ke Bing...")
        response = await self.client.get(initiation_url, follow_redirects=True)
        response.raise_for_status()

        if "images/create/async/results/" not in str(response.url):
            raise Exception('Gagal memulai sesi pembuatan gambar. Periksa validitas dan kelengkapan cookie Anda.')
        
        polling_url = str(response.url).replace(self.base_url, "")
        self.__log(f"{self.log.GREEN}Sesi berhasil dibuat, URL Polling: {polling_url}")

        image_urls = await self._poll_for_images(polling_url)
        self.__log(f"{self.log.GREEN}Ditemukan {len(image_urls)} gambar final.")

        return image_urls
