import asyncio
import os
import re
import time
from urllib.parse import quote, urlencode, parse_qs, urlparse

import httpx
import fake_useragent

from ..utils.logger import LoggerHandler


class ImageGenerator:
    def __init__(self, cookies_file_path: str = "cookies.txt", logging_enabled: bool = True):
        self.all_cookies = self._parse_cookie_file(cookies_file_path)
        self.auth_cookie_U = self.all_cookies.get("_U")
        self.auth_cookie_KievRPSSecAuth = self.all_cookies.get("KievRPSSecAuth")

        if not self.auth_cookie_U:
            raise ValueError("File cookie harus berisi cookie '_U'.")

        self.base_url = "https://www.bing.com"
        self.client = self._prepare_client()
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()

    def _prepare_client(self):
        cookie_jar = httpx.Cookies()
        cookie_jar.set("_U", self.auth_cookie_U, domain=".bing.com")
        if self.auth_cookie_KievRPSSecAuth:
            cookie_jar.set("KievRPSSecAuth", self.auth_cookie_KievRPSSecAuth, domain=".bing.com")

        headers = {
            'User-Agent': fake_useragent.UserAgent().random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': f"{self.base_url}/images/create",
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
                if line.strip().startswith("#") or line.strip() == "":
                    continue

                parts = line.strip().split("\t")
                if len(parts) >= 7:
                    domain = parts[0]
                    if ".bing.com" in domain:
                        cookie_name = parts[5]
                        cookie_value = parts[6]
                        cookies_dict[cookie_name] = cookie_value

        return cookies_dict

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    async def _get_balance(self):
        try:
            response = await self.client.get("/images/create", follow_redirects=True)
            response.raise_for_status()
            match = re.search(r'<div id="reward_c" data-tb="(\d+)"', response.text)
            if match:
                return 15 - int(match.group(1))
            return 0
        except Exception:
            raise Exception('Cookie otentikasi gagal! Pastikan _U dan KievRPSSecAuth (jika ada) valid.')

    async def _fetch_images_from_result(self, polling_url):
        start_time = time.time()
        while time.time() - start_time < 180:
            self.__log(f"{self.log.YELLOW}Meminta hasil gambar...")
            response = await self.client.get(polling_url)
            
            if response.status_code == 200:
                if 'src="https://th.bing.com/th/id/' in response.text:
                    src_urls = re.findall(r'src="([^"]+)"', response.text)
                    if src_urls:
                        return [url.split('?')[0] for url in src_urls if '?' in url]
                elif 'gil_err_msg' in response.text:
                    raise Exception("Bing mengembalikan error, mungkin karena kebijakan konten.")
            
            await asyncio.sleep(5)
        raise Exception("Waktu tunggu habis saat mengambil gambar.")
    
    async def generate(self, prompt: str):
        self.__log(f"{self.log.GREEN}Memulai pembuatan gambar untuk prompt: '{prompt}'")
        
        coins = await self._get_balance()
        rt_value = '4' if coins > 0 else '3'
        
        params = {'q': prompt, 'rt': rt_value, 'FORM': 'GENCRE'}
        creation_url = f'/images/create?{urlencode(params)}'
        
        self.__log(f"{self.log.CYAN}Mengirim permintaan ke Bing...")
        response = await self.client.post(creation_url)
        response.raise_for_status()

        final_url = str(response.url)
        if "create/async/results/" not in final_url:
            if 'data-clarity-tag="BlockedByContentPolicy"' in response.text:
                raise Exception('Prompt Anda ditolak karena alasan kebijakan konten.')
            raise Exception('Gagal mendapatkan URL hasil. Periksa validitas cookie Anda.')

        request_id_match = re.search(r'id=([^&]+)', final_url)
        if not request_id_match:
             raise Exception('Gagal mengekstrak ID permintaan dari URL hasil.')
             
        request_id = request_id_match.group(1)
        self.__log(f"{self.log.GREEN}Permintaan berhasil, ID: {request_id}")
        
        polling_url = str(response.url).replace(self.base_url, "")
        
        image_urls = await self._fetch_images_from_result(polling_url)
        self.__log(f"{self.log.GREEN}Ditemukan {len(image_urls)} gambar final.")

        return image_urls
