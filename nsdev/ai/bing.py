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
        self.all_cookies = self._parse_cookie_file(cookies_file_path)

        self.base_url = "https://www.bing.com"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            cookies=self.all_cookies,
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

    def _parse_cookie_file(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Cookie file not found: {file_path}")

        cookies_dict = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("#") or line.strip() == "":
                    continue

                parts = line.strip().split("\t")
                if len(parts) == 7:
                    cookie_name = parts[5]
                    cookie_value = parts[6]
                    cookies_dict[cookie_name] = cookie_value

        return cookies_dict

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
            self.__log(f"{self.log.RED}Response: {response.text}...")
            raise Exception("Permintaan gagal. Pastikan cookie _U valid dan tidak kadaluarsa.")

        redirect_url = response.headers.get("Location")
        if not redirect_url or "id=" not in redirect_url:
            self.__log(f"{self.log.RED}Redirect URL: {redirect_url}")
            raise Exception("Gagal mendapatkan ID permintaan dari redirect. Prompt mungkin diblokir.")

        request_id_match = re.search(r"id=([^&]+)", redirect_url)
        if not request_id_match:
            raise Exception("Gagal mendapatkan ID permintaan dari redirect. Prompt mungkin diblokir.")

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
                self.__log(f"{self.log.YELLOW}Status polling tidak 200, mencoba lagi...")
                await asyncio.sleep(2)
                continue

            if "errorMessage" in poll_response.text:
                error_message_match = re.search(r'<div id="gil_err_msg">([^<]+)</div>', poll_response.text)
                if error_message_match:
                    raise Exception(f"Bing error: {error_message_match.group(1).strip()}")
                else:
                    raise Exception(f"Bing error (unknown details): {poll_response.text[:250]}...")

            if (
                re.search(r'data-preloader="true"', poll_response.text)
                or re.search(r"Your images are being created", poll_response.text, re.IGNORECASE)
                or re.search(
                    r'<div[^>]*class="img_sugg_info"[^>]*>We are working on your request',
                    poll_response.text,
                    re.IGNORECASE,
                )
                or re.search(
                    r'<div[^>]*class="gil_items_status"[^>]*>([^<]+?)</div>', poll_response.text, re.IGNORECASE
                )
            ):
                self.__log(f"{self.log.YELLOW}Gambar masih dalam proses rendering. Menunggu...")
                await asyncio.sleep(3)
                continue

            image_urls_raw = re.findall(
                r'(?:<a[^>]+href="[^"]+"[^>]*>)?<img[^>]*src="(https?://th.bing.com/th/id/OIP.[^"]+)"[^>]*>',
                poll_response.text,
            )

            processed_urls = []

            for url_group in image_urls_raw:
                img_src_url = url_group

                parsed_url = urllib.parse.urlparse(img_src_url)
                query_params = urllib.parse.parse_qs(parsed_url.query)

                query_params["w"] = ["1024"]
                query_params["h"] = ["1024"]
                query_params["qlt"] = ["90"]
                query_params["dpr"] = ["1"]

                reconstructed_query = urllib.parse.urlencode(query_params, doseq=True)
                high_res_url = urllib.parse.urlunparse(parsed_url._replace(query=reconstructed_query))

                processed_urls.append(high_res_url)

            processed_urls = list(set(processed_urls))

            if len(processed_urls) < 4:
                self.__log(
                    f"{self.log.YELLOW}Ditemukan {len(processed_urls)} gambar, menunggu {4 - len(processed_urls)} gambar lainnya."
                )
                await asyncio.sleep(3)
                continue

            if processed_urls:
                self.__log(
                    f"{self.log.GREEN}Ditemukan {len(processed_urls)} gambar final. Total waktu: {round(time.time() - start_time, 2)}s."
                )
                return processed_urls

            await asyncio.sleep(3)
