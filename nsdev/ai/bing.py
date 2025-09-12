import asyncio
import os
import re
import time
import urllib.parse
from typing import Dict, List

import fake_useragent
import httpx

from ..utils.logger import LoggerHandler


class ImageGenerator:
    def __init__(self, cookies_file_path: str = "cookies.txt", logging_enabled: bool = True):
        self.cookies = self._parse_cookie_file(cookies_file_path)

        self.base_url = "https://www.bing.com"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            cookies=self.cookies,
            headers={
                "User-Agent": fake_useragent.UserAgent().random,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": f"{self.base_url}/images/create",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "TE": "trailers",
                "Connection": "keep-alive",
            },
            follow_redirects=False,
            timeout=200,
        )
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()

    def _parse_cookie_file(self, file_path: str) -> Dict[str, str]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Cookie file not found: {file_path}")

        cookies = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("#") or line.strip() == "":
                    continue

                parts = line.strip().split("\t")
                if len(parts) == 7 and "bing.com" in parts[0]:
                    cookies[parts[5]] = parts[6]
        
        if not cookies:
            raise ValueError(f"No cookies found in {file_path}")
        return cookies

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    async def generate(self, prompt: str, max_wait_seconds: int = 300) -> List[str]:
        if not prompt:
            raise ValueError("Prompt tidak boleh kosong.")

        start_time = time.time()
        self.__log(f"{self.log.GREEN}Memulai pembuatan gambar untuk prompt: '{prompt}'")
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"/images/create?q={encoded_prompt}&rt=4&FORM=GENCRE"

        try:
            response = await self.client.post(url)
        except httpx.RequestError as e:
            raise Exception(f"Gagal mengirim permintaan pembuatan gambar: {e}")

        if response.status_code != 302:
            self.__log(f"{self.log.RED}Status code tidak valid: {response.status_code}. Mungkin cookie tidak valid.")
            self.__log(f"{self.log.RED}Response: {response.text[:500]}...")
            raise Exception("Permintaan gagal. Pastikan cookie valid dan tidak kadaluarsa.")

        redirect_url = response.headers.get("Location")
        if not redirect_url or "id=" not in redirect_url:
            raise Exception("Gagal mendapatkan ID permintaan dari redirect. Prompt mungkin diblokir.")

        request_id = re.search(r"id=([^&]+)", redirect_url).group(1)
        self.__log(f"{self.log.GREEN}Permintaan berhasil dikirim. ID: {request_id}")
        polling_url = f"/images/create/async/results/{request_id}?q={encoded_prompt}"
        self.__log(f"{self.log.GREEN}Menunggu hasil gambar...")
        wait_start_time = time.time()

        while True:
            if time.time() - wait_start_time > max_wait_seconds:
                raise Exception(f"Waktu tunggu habis ({max_wait_seconds} detik).")

            try:
                poll_response = await self.client.get(polling_url)
            except httpx.RequestError as e:
                self.__log(f"{self.log.YELLOW}Gagal polling, mencoba lagi... Error: {e}")
                await asyncio.sleep(2)
                continue

            if poll_response.status_code != 200:
                self.__log(f"{self.log.YELLOW}Status polling tidak 200, mencoba lagi. Status: {poll_response.status_code}")
                await asyncio.sleep(2)
                continue

            if "errorMessage" in poll_response.text:
                error_message_match = re.search(r'<div id="gil_err_msg">([^<]+)</div>', poll_response.text)
                error_message = error_message_match.group(1).strip() if error_message_match else "Unknown error from Bing"
                raise Exception(f"Bing error: {error_message}")

            image_urls = re.findall(r'src="([^"]+)"', poll_response.text)
            
            processed_urls = list(set([url.split("?w=")[0] for url in image_urls if "tse" in url and "id=g" in url]))

            if processed_urls:
                first_image_url = processed_urls[0]
                try:
                    head_response = await self.client.head(first_image_url, follow_redirects=True, timeout=10)
                    if head_response.status_code == 200 and 'content-type' in head_response.headers and 'image' in head_response.headers['content-type']:
                        self.__log(
                            f"{self.log.GREEN}Ditemukan {len(processed_urls)} gambar. Total waktu: {round(time.time() - start_time, 2)}s."
                        )
                        return processed_urls
                    else:
                        self.__log(f"{self.log.YELLOW}Gambar ditemukan tapi belum siap (status: {head_response.status_code}, content-type: {head_response.headers.get('content-type')}). Menunggu...")
                except httpx.RequestError as e:
                    self.__log(f"{self.log.YELLOW}Gagal memeriksa header gambar, mencoba lagi. Error: {e}")
                
            await asyncio.sleep(3)
            redirect_url = response.headers.get("Location")
        if not redirect_url or "id=" not in redirect_url:
            raise Exception("Gagal mendapatkan ID permintaan dari redirect. Prompt mungkin diblokir.")

        request_id = re.search(r"id=([^&]+)", redirect_url).group(1)
        self.__log(f"{self.log.GREEN}Permintaan berhasil dikirim. ID: {request_id}")
        polling_url = f"/images/create/async/results/{request_id}?q={encoded_prompt}"
        self.__log(f"{self.log.GREEN}Menunggu hasil gambar...")
        wait_start_time = time.time()

        final_images = []
        while True:
            if time.time() - wait_start_time > max_wait_seconds:
                raise Exception(f"Waktu tunggu habis ({max_wait_seconds} detik).")

            try:
                poll_response = await self.client.get(polling_url)
            except httpx.RequestError as e:
                self.__log(f"{self.log.YELLOW}Gagal polling, mencoba lagi... Error: {e}")
                await asyncio.sleep(2)
                continue

            if poll_response.status_code != 200:
                self.__log(f"{self.log.YELLOW}Status polling tidak 200, mencoba lagi...")
                await asyncio.sleep(2)
                continue

            if "errorMessage" in poll_response.text:
                error_message = re.search(r'<div id="gil_err_msg">([^<]+)</div>', poll_response.text)
                raise Exception(f"Bing error: {error_message.group(1)}")

            image_urls = re.findall(r'src="([^"]+)"', poll_response.text)
            processed_urls = list(set([url.split("?w=")[0] for url in image_urls if "tse" in url]))

            if processed_urls:
                clear_urls = [u for u in processed_urls if not re.search(r"(pid|jpeg|png)&w=\d+&h=\d+&c=\d+", u)]
                if clear_urls:
                    final_images = clear_urls
                    if len(final_images) >= 4:
                        self.__log(
                            f"{self.log.GREEN}Ditemukan {len(final_images)} gambar final. Total waktu: {round(time.time() - start_time, 2)}s."
                        )
                        return final_images
            await asyncio.sleep(3)
