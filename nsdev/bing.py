import asyncio
import re
import time
import urllib.parse
import httpx
import fake_useragent
from .logger import LoggerHandler

class ImageGenerator:
    def __init__(
        self,
        auth_cookie_u: str,
        logging_enabled: bool = True,
    ):
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

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    async def generate(self, prompt: str, num_images: int = 4, max_wait_seconds: int = 300):
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
            self.__log(f"{self.log.RED}Response: {response.text[:250]}...")
            raise Exception("Permintaan gagal. Pastikan cookie _U valid dan tidak kadaluarsa.")
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
                self.__log(f"{self.log.YELLOW}Status polling tidak 200, mencoba lagi...")
                await asyncio.sleep(2)
                continue
            if "errorMessage" in poll_response.text:
                error_message = re.search(r'<div id="gil_err_msg">([^<]+)</div>', poll_response.text)
                raise Exception(f"Bing error: {error_message.group(1)}")
            image_urls = re.findall(r'src="([^"]+)"', poll_response.text)
            processed_urls = list(set([url.split("?w=")[0] for url in image_urls if "tse" in url]))
            if processed_urls:
                self.__log(f"{self.log.GREEN}Ditemukan {len(processed_urls)} gambar. Total waktu: {round(time.time() - start_time, 2)}s.")
                return processed_urls[:num_images]
            await asyncio.sleep(3)
