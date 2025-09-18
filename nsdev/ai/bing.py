import asyncio
import os
import re
import time
from urllib.parse import quote, urlencode

import httpx
import fake_useragent

from ..utils.logger import LoggerHandler

class ImageGenerator:
    def __init__(self, cookies_file_path: str = "cookies.txt", logging_enabled: bool = True):
        self.raw_cookie_string = self._read_first_line_of_cookie_file(cookies_file_path)
        if not self.raw_cookie_string:
            raise ValueError(f"File cookie '{cookies_file_path}' kosong atau tidak ditemukan.")

        self.base_url = "https://www.bing.com"
        self.client = self._prepare_client()
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()

    def _read_first_line_of_cookie_file(self, file_path: str) -> str or None:
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.strip().startswith("#"):
                    return line.strip()
        return None
    
    def _prepare_client(self):
        headers = {
            'User-Agent': fake_useragent.UserAgent().random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f"{self.base_url}/create",
            'Cookie': self.raw_cookie_string,
        }
        
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            follow_redirects=True,
            timeout=200,
        )

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    async def _fetch_images_from_result(self, polling_url: str):
        start_time = time.time()
        while time.time() - start_time < 240:
            self.__log(f"{self.log.YELLOW}Meminta hasil gambar...")
            response = await self.client.get(polling_url)
            
            if response.status_code == 200:
                if 'class="gi_err_msg"' in response.text:
                    raise Exception("Bing mengembalikan error: Kebijakan konten mungkin telah dilanggar.")

                image_urls = re.findall(r'src="([^"]+)"', response.text)
                final_images = [url.split('?')[0] for url in image_urls if re.search(r'th.bing.com/th/id/OIG', url)]

                if final_images:
                    return final_images

            await asyncio.sleep(5)
        raise Exception("Waktu tunggu habis saat mengambil gambar.")
    
    async def generate(self, prompt: str):
        self.__log(f"{self.log.GREEN}Memulai pembuatan gambar untuk prompt: '{prompt}'")
        
        encoded_prompt = quote(prompt)
        creation_url = f'/images/create?q={encoded_prompt}&rt=4&FORM=GENCRE'
        
        self.__log(f"{self.log.CYAN}Mengirim permintaan pembuatan ke Bing...")
        
        await self.client.get("/images/create")
        
        response = await self.client.post(creation_url, follow_redirects=True)
        response.raise_for_status()
        
        if "proccessing" in str(response.url) or "results" in str(response.url):
            polling_url = str(response.url).replace(self.base_url, "")
        else: # Mencari redirect di body jika tidak ada di URL
            redirect_match = re.search(r'id="redirect_url" value="([^"]+)"', response.text)
            if not redirect_match:
                 if 'class="gi_err_msg"' in response.text:
                    raise Exception("Bing menolak prompt. Kebijakan konten atau cookie tidak valid.")
                 raise Exception("Gagal menemukan URL redirect hasil. Periksa cookie Anda.")
            polling_url = redirect_match.group(1)

        self.__log(f"{self.log.GREEN}Permintaan berhasil dikirim. URL Polling: {polling_url}")
        
        image_urls = await self._fetch_images_from_result(polling_url)
        self.__log(f"{self.log.GREEN}Ditemukan {len(image_urls)} gambar final.")

        return image_urls
