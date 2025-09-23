import asyncio
import os
import re
import time
from http.cookiejar import MozillaCookieJar
from urllib.parse import quote

import httpx

from ..utils.logger import LoggerHandler


class ImageGenerator:
    def __init__(self, cookies_file_path: str = "cookies.txt", logging_enabled: bool = True):
        self.client = self._prepare_client(cookies_file_path)
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()

    def _prepare_client(self, cookie_path):
        if not os.path.exists(cookie_path):
            raise FileNotFoundError(f"File cookie tidak ditemukan: {cookie_path}")

        cj = MozillaCookieJar(cookie_path)
        cj.load(ignore_discard=True, ignore_expires=True)

        cookies = httpx.Cookies()
        for cookie in cj:
            cookies.set(cookie.name, cookie.value, domain=cookie.domain, path=cookie.path)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.bing.com",
            "Referer": "https://www.bing.com/images/create",
        }

        return httpx.AsyncClient(
            base_url="https://www.bing.com",
            headers=headers,
            cookies=cookies,
            timeout=httpx.Timeout(300.0),
            follow_redirects=True,
        )

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    async def generate(self, prompt: str, retries: int = 3):
        url_prompt = quote(prompt)

        dalle_url = f"/images/create?q={url_prompt}&rt=4&mdl=0&ar=1&FORM=GENCRE"

        for attempt in range(1, retries + 1):
            self.__log(f"{self.log.CYAN}Mengirim permintaan ke Bing (Percobaan {attempt}/{retries})...")

            request = self.client.build_request(
                "POST", dalle_url, data={"q": url_prompt, "qs": "ds"}
            )

            response = await self.client.send(request, follow_redirects=False)

            if response.status_code == 302:
                redirect_url = response.headers.get("Location")
                if not redirect_url:
                    raise Exception("Redirect diterima, tetapi tanpa header Location.")
                try:
                    request_id = re.search(r"id=([^&]+)", redirect_url).group(1)
                    self.__log(f"{self.log.GREEN}Berhasil mendapatkan ID permintaan: {request_id}")
                    break
                except (AttributeError, IndexError):
                    raise Exception("Gagal mengekstrak ID permintaan dari URL redirect.")
            else:
                if attempt == retries:
                    raise Exception(
                        f"Gagal mendapatkan redirect setelah {retries} percobaan. Status: {response.status_code}"
                    )
                await asyncio.sleep(2)

        polling_url = f"/images/create/async/results/{request_id}?q={url_prompt}"
        start_time = time.time()
        self.__log(f"{self.log.YELLOW}Menunggu hasil gambar (mode DALL·E)...")

        while time.time() - start_time < 180:
            poll_response = await self.client.get(polling_url)

            if poll_response.status_code != 200:
                self.__log(f"{self.log.YELLOW}Status polling tidak 200 ({poll_response.status_code}), mencoba lagi...")
                await asyncio.sleep(5)
                continue

            if "gil_err_msg" in poll_response.text or "errorMessage" in poll_response.text:
                raise Exception("Bing mengembalikan error, kemungkinan karena kebijakan konten.")

            links = re.findall(r'src="([^"]+)"', poll_response.text)
            valid_links = [link.split("?")[0] for link in links if "tse" in link]

            if valid_links:
                unique_links = sorted(list(set(valid_links)))
                self.__log(f"{self.log.GREEN}Ditemukan {len(unique_links)} gambar (DALL·E).")
                return unique_links

            await asyncio.sleep(5)

        raise Exception("Waktu tunggu habis saat menunggu gambar.")
