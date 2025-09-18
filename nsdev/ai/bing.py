import asyncio
import os
import re
import time
from urllib.parse import urlencode

import httpx
import fake_useragent

from ..utils.logger import LoggerHandler


class ImageGenerator:
    def __init__(self, cookies_file_path: str = "cookies/Bing.txt", logging_enabled: bool = True):
        self.all_cookies = self._parse_cookie_file(cookies_file_path)
        self.required_cookies = [
            'MUID', 'ANON', '_U', 'MSPTC', 'ak_bmsc', 
            '_RwBf', '_SS', 'SRCHUSR', 'SRCHUID', 'SRCHHPGUSR'
        ]
        
        self.base_url = "https://www.bing.com"
        self.client = self._prepare_client()
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()

    def _prepare_client(self):
        filtered_cookies = {k: v for k, v in self.all_cookies.items() if k in self.required_cookies}
        if "_U" not in filtered_cookies:
            raise ValueError("File cookie harus berisi cookie '_U'.")

        cookie_jar = httpx.Cookies()
        for name, value in filtered_cookies.items():
            cookie_jar.set(name, value, domain=".bing.com")

        headers = {
            'User-Agent': fake_useragent.UserAgent().random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f"{self.base_url}/create",
            'Origin': self.base_url,
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
        }
        
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            cookies=cookie_jar,
            follow_redirects=True,
            timeout=200,
        )

    def _parse_cookie_file(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File cookie tidak ditemukan: {file_path}")

        cookies_dict = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("#") or not line.strip():
                    continue

                parts = line.strip().split('\t')
                if len(parts) >= 7 and '.bing.com' in parts[0]:
                    cookies_dict[parts[5]] = parts[6]
        
        return cookies_dict

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    async def _fetch_images_from_result(self, polling_url: str, prompt: str):
        start_time = time.time()
        while time.time() - start_time < 180:
            self.__log(f"{self.log.YELLOW}Meminta hasil gambar...")
            response = await self.client.get(polling_url)
            
            if response.status_code != 200:
                await asyncio.sleep(5)
                continue

            if 'Your images are being created' in response.text or 'data-preloader="true"' in response.text:
                 self.__log(f"{self.log.YELLOW}Gambar masih dalam proses rendering...")
                 await asyncio.sleep(5)
                 continue

            if 'src="https://th.bing.com/th/id/' in response.text:
                image_urls = re.findall(r'<img class="mimg".*?src="([^"]+)"', response.text)
                if image_urls:
                    cleaned_urls = [re.sub(r'&w=\d+&h=\d+&c=\d+&rs=\d+&qlt=\d+&o=\d+&dpr=\d+&pid=ImgGn', '', url) for url in image_urls]
                    return cleaned_urls

            if 'gil_err_msg' in response.text:
                raise Exception("Bing mengembalikan error, mungkin karena kebijakan konten.")
            
            await asyncio.sleep(5)

        raise Exception("Waktu tunggu habis saat mengambil gambar.")
    
    async def generate(self, prompt: str):
        self.__log(f"{self.log.GREEN}Memulai pembuatan gambar untuk prompt: '{prompt}'")
        
        encoded_prompt = urlencode({'q': prompt})
        
        creation_url = f'/images/create?{encoded_prompt}&rt=4&FORM=GENCRE'
        
        self.__log(f"{self.log.CYAN}Mengirim permintaan ke Bing...")
        response = await self.client.get(creation_url)
        response.raise_for_status()
        
        if "create/async/results/" not in str(response.url):
            if 'ContentData' in response.text and 'Block' in response.text:
                raise Exception('Prompt Anda ditolak karena alasan kebijakan konten. ' + str(response.url))
            raise Exception('Gagal mendapatkan URL hasil. Periksa validitas cookie Anda. ' + str(response.url))

        polling_url = str(response.url)
        self.__log(f"{self.log.GREEN}Permintaan berhasil, URL polling: {polling_url.replace(self.base_url, '')}")
        
        image_urls = await self._fetch_images_from_result(polling_url, prompt)
        
        if not image_urls:
            raise Exception("Tidak ada gambar yang dihasilkan. Coba lagi atau perbarui cookie.")

        self.__log(f"{self.log.GREEN}Ditemukan {len(image_urls)} gambar final.")
        return image_urls
