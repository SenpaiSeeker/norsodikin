import asyncio
import os
import re
import time
import urllib.parse

import fake_useragent
import httpx

from ..utils.logger import LoggerHandler


class ImageGenerator:
    def __init__(self, cookies_file_path: str = "cookies.txt", logging_enabled: bool = True):
        auth_cookie_u = self._parse_cookie_file(cookies_file_path)

        self.base_url = "https://www.bing.com"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            cookies={"_U": auth_cookie_u},
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

    def _parse_cookie_file(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Cookie file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("#") or line.strip() == "":
                    continue

                parts = line.strip().split("\t")
                if len(parts) == 7 and "bing.com" in parts[0] and parts[5] == "_U":
                    return parts[6]

        raise ValueError(f"Could not find the '_U' cookie for bing.com in {file_path}")

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    async def generate(self, prompt: str, max_wait_seconds: int = 300):
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
            if "Unsupported prompt" in response.text or "This prompt may result in an image that is inappropriate." in response.text:
                 raise Exception("Permintaan gagal: Prompt diblokir oleh Bing (Unsupported/Inappropriate prompt).")
            if "The content you provided was in violation" in response.text:
                raise Exception("Permintaan gagal: Prompt diblokir oleh Bing karena pelanggaran konten.")
            raise Exception("Permintaan gagal. Pastikan cookie _U valid dan tidak kadaluarsa, atau coba prompt yang berbeda.")

        redirect_url = response.headers.get("Location")
        if not redirect_url:
            raise Exception("Gagal mendapatkan redirect URL. Pastikan cookie _U valid dan prompt tidak diblokir.")
        
        request_id_match = re.search(r"id=([^&]+)", redirect_url)
        if not request_id_match:
            self.__log(f"{self.log.RED}Redirect URL tidak mengandung ID: {redirect_url}. Mungkin prompt diblokir atau ada masalah lain.")
            raise Exception("Gagal mendapatkan ID permintaan dari redirect. Prompt mungkin diblokir atau ada masalah tak terduga.")

        request_id = request_id_match.group(1)
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
                self.__log(f"{self.log.YELLOW}Status polling tidak 200 ({poll_response.status_code}), mencoba lagi...")
                await asyncio.sleep(2)
                continue

            if "errorMessage" in poll_response.text:
                error_message_match = re.search(r'<div id="gil_err_msg">([^<]+)</div>', poll_response.text)
                if error_message_match:
                    raise Exception(f"Bing error: {error_message_match.group(1).strip()}")
                else:
                    raise Exception(f"Bing error: Unknown error in async response: {poll_response.text[:250]}...")
            
            blob_urls = re.findall(r'href="(https://[^"]*bing.com/images/blob\?bcid=[^"]*)"', poll_response.text)
            
            processed_urls = list(set(blob_urls))

            if processed_urls:
                self.__log(
                    f"{self.log.GREEN}Ditemukan {len(processed_urls)} gambar final. Total waktu: {round(time.time() - start_time, 2)}s."
                )
                return processed_urls
            
            self.__log(f"{self.log.CYAN}Gambar masih dalam proses rendering atau belum siap. Menunggu... ({round(time.time() - wait_start_time)}s)")
            await asyncio.sleep(3)
