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
        self.cookies = self._parse_and_filter_cookies(cookies_file_path)
        if not self.cookies.get("_U"):
            raise ValueError("File cookie harus berisi cookie '_U' yang valid.")

        self.base_url = "https://www.bing.com"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            cookies=self.cookies,
            headers={"User-Agent": fake_useragent.UserAgent().random},
            follow_redirects=True,
            timeout=200,
        )
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()

    def _parse_and_filter_cookies(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File cookie tidak ditemukan: {file_path}")

        required_cookies = ['MUID', 'ANON', '_U', 'MSPTC', 'ak_bmsc', '_RwBf', '_SS', 'SRCHUSR', 'SRCHUID', 'SRCHHPGUSR']
        cookies_dict = {}

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("#") or line.strip() == "":
                    continue

                parts = line.strip().split("\t")
                if len(parts) >= 7:
                    cookie_name = parts[5]
                    if cookie_name in required_cookies:
                        cookies_dict[cookie_name] = parts[6]

        return cookies_dict

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    async def generate(self, prompt: str):
        self.__log(f"{self.log.GREEN}Memulai pembuatan gambar untuk prompt: '{prompt}'")
        
        encoded_prompt = quote(prompt)
        url = f"/images/create?q={encoded_prompt}&rt=4&FORM=GENCRE"
        
        self.__log(f"{self.log.CYAN}Mengirim permintaan ke Bing...")
        
        try:
            response = await self.client.get(url, follow_redirects=True)
            response.raise_for_status()

            if "auth" in str(response.url):
                 raise Exception("Otentikasi cookie gagal. Harap perbarui cookie Anda.")

            content = response.text
            id_match = re.search(r'id=([^&]+)', str(response.url))
            if not id_match:
                 if "Apologies, but we're unable to generate this prompt." in content:
                     raise Exception('Prompt ditolak oleh kebijakan konten Bing.')
                 raise Exception('Gagal mendapatkan ID permintaan dari URL hasil. Cookie mungkin tidak valid.')
            
            request_id = id_match.group(1)
            self.__log(f"{self.log.GREEN}Permintaan berhasil, ID: {request_id}")

            polling_url = f"/images/create/async/results/{request_id}?q={encoded_prompt}"
            
            start_time = time.time()
            while time.time() - start_time < 180:
                self.__log(f"{self.log.YELLOW}Meminta hasil gambar...")
                poll_response = await self.client.get(polling_url)
                
                if poll_response.status_code == 200:
                    if 'src="https://th.bing.com/th/id/' in poll_response.text:
                        src_urls = re.findall(r'src="([^"]+)"', poll_response.text)
                        valid_urls = [url.split('?')[0] for url in src_urls if '?' in url and 'r.bing.com' not in url]
                        
                        if valid_urls:
                             self.__log(f"{self.log.GREEN}Ditemukan {len(valid_urls)} gambar final.")
                             return valid_urls

                await asyncio.sleep(5)
                
            raise Exception("Waktu tunggu habis saat mengambil gambar.")
        
        except httpx.HTTPStatusError as e:
            raise Exception(f"Permintaan ke Bing gagal dengan status {e.response.status_code}.")
        except Exception as e:
            raise e
