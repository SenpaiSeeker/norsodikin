import asyncio
import os
import re
import time
import urllib.parse
from typing import List

import fake_useragent
import httpx

from ..utils.logger import LoggerHandler


class ImageGenerator:
    def __init__(self, cookies_file_path: str = "cookies.txt", logging_enabled: bool = True):
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()

        self.cookies: httpx.Cookies = self._parse_netscape_cookies(cookies_file_path)

        self.base_url = "https://www.bing.com"
        user_agent_header = fake_useragent.UserAgent().random

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            cookies=self.cookies,
            headers={
                "User-Agent": user_agent_header,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": f"{self.base_url}/images/create",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Connection": "keep-alive",
            },
            follow_redirects=False,
            timeout=200,
        )


    def _parse_netscape_cookies(self, file_path: str) -> httpx.Cookies:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Cookie file not found: {file_path}")

        cookies = httpx.Cookies()
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split("\t")
                if len(parts) == 7:
                    try:
                        name = parts[5]
                        value = parts[6]
                        cookies[name] = value
                    except (IndexError, ValueError) as e:
                        self.log.print(f"{self.log.YELLOW}Failed to parse cookie line: '{line}'. Error: {e}")
                        continue
                else:
                    self.log.print(
                        f"{self.log.YELLOW}Skipping malformed cookie line: '{line}' (expected 7 parts, got {len(parts)})",
                    )

        if not cookies:
            raise ValueError(f"No valid cookies found in {file_path}. Make sure the file is correctly formatted.")

        self.log.print(f"{self.log.BLUE}Berhasil memuat {len(cookies)} cookie dari {file_path}")
        if "_U" not in cookies:
            raise ValueError(f"Cookie '_U' yang penting untuk autentikasi tidak ditemukan di {file_path}. Harap pastikan file cookie Anda berisi cookie _U yang valid.")

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
            post_headers = {
                **self.client.headers,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            }
            response = await self.client.post(url, headers=post_headers, data="")
        except httpx.RequestError as e:
            raise Exception(f"Gagal mengirim permintaan pembuatan gambar: {e}")

        if response.status_code == 302:
            redirect_url = response.headers.get("Location")
            if not redirect_url or "id=" not in redirect_url:
                self.__log(
                    f"{self.log.RED}Gagal mendapatkan ID permintaan dari redirect. Prompt mungkin diblokir atau cookie tidak valid/kedaluwarsa. Redirect URL: {redirect_url}"
                )
                self.__log(f"{self.log.RED}Respons (awal): {response.text[:250]}...")
                raise Exception("Gagal mendapatkan ID permintaan dari redirect. Prompt mungkin diblokir atau ada masalah lain.")

            request_id_match = re.search(r"id=([^&]+)", redirect_url)
            if not request_id_match:
                self.__log(f"{self.log.RED}ID permintaan tidak ditemukan di redirect URL: {redirect_url}")
                raise Exception("ID permintaan tidak ditemukan di redirect URL.")

            request_id = request_id_match.group(1)
            self.__log(f"{self.log.GREEN}Permintaan pembuatan berhasil dikirim. ID: {request_id}")
            polling_url = f"/images/create/async/results/{request_id}?q={encoded_prompt}"
        elif response.status_code == 200:
            self.__log(f"{self.log.YELLOW}Menerima status code 200 langsung. Mencari request ID dalam URL saat ini.")
            current_url = str(response.url)
            request_id_match = re.search(r"id=([^&]+)", current_url)
            if request_id_match:
                request_id = request_id_match.group(1)
                self.__log(f"{self.log.GREEN}Request ID ditemukan di URL: {request_id}")
                polling_url = f"/images/create/async/results/{request_id}?q={encoded_prompt}"
            else:
                self.__log(f"{self.log.RED}Gagal menemukan request ID dari status 200 respons.")
                self.__log(f"{self.log.RED}Respons (awal): {response.text[:250]}...")
                raise Exception("Permintaan gagal. Status 200 tetapi gagal mendapatkan ID permintaan.")
        else:
            self.__log(
                f"{self.log.RED}Status code tidak valid: {response.status_code}. Mungkin cookie tidak valid atau layanan sedang bermasalah."
            )
            self.__log(f"{self.log.RED}Respons (awal): {response.text[:500]}...")
            raise Exception("Permintaan gagal. Pastikan cookie _U valid dan tidak kadaluarsa.")

        self.__log(f"{self.log.GREEN}Menunggu hasil gambar. Polling URL: {polling_url}")
        wait_start_time = time.time()

        rendering_keywords = [
            "sedang membuat gambar anda",
            "generating your images",
            "Please wait while your images are being generated",
            "Creating images",
            "inProgress",
            "creating...",
        ]

        while True:
            elapsed_time = time.time() - wait_start_time
            if elapsed_time > max_wait_seconds:
                raise Exception(f"Waktu tunggu habis ({max_wait_seconds} detik) untuk mendapatkan hasil gambar.")

            try:
                poll_response = await self.client.get(polling_url)
            except httpx.RequestError as e:
                self.__log(f"{self.log.YELLOW}Gagal melakukan polling, mencoba lagi... Error: {e}")
                await asyncio.sleep(3)
                continue

            if poll_response.status_code != 200:
                self.__log(
                    f"{self.log.YELLOW}Status polling tidak 200 ({poll_response.status_code}), mencoba lagi. Respons (polling): {poll_response.text[:100]}..."
                )
                await asyncio.sleep(3)
                continue

            response_text = poll_response.text

            if "errorMessage" in response_text or '<div id="gil_err_msg">' in response_text:
                error_message_match = re.search(r'<div id="gil_err_msg">([^<]+)</div>', response_text)
                if error_message_match:
                    error_msg = error_message_match.group(1).strip()
                    self.__log(f"{self.log.RED}Kesalahan dari Bing: {error_msg}")
                    raise Exception(f"Kesalahan Bing: {error_msg}")
                else:
                    self.__log(f"{self.log.RED}Kesalahan umum dari Bing, tidak dapat mengekstrak pesan spesifik. Respons (error): {response_text[:200]}")
                    raise Exception(f"Kesalahan umum Bing: {response_text[:200]}")

            is_rendering = False
            for keyword in rendering_keywords:
                if keyword.lower() in response_text.lower():
                    is_rendering = True
                    break

            if is_rendering:
                self.__log(f"{self.log.YELLOW}Gambar masih dalam proses rendering. Menunggu... ({int(elapsed_time)}/{max_wait_seconds}s)")
                await asyncio.sleep(5)
                continue

            image_urls_matches = re.findall(
                r'(?:src|data-src)="([^"]*?(?:th\.bing\.com/th/id/OIG\w+|tse\d?\.mm\.bing\.net/th/\?id=OIG\w+)[^"]*?)"',
                response_text,
                re.IGNORECASE,
            )

            processed_urls = []
            seen_base_urls = set()
            for url in image_urls_matches:
                parsed_url = urllib.parse.urlparse(url)
                if "OIG" in url.upper():
                    oig_id_match = re.search(r'OIG(\w+)', parsed_url.path + parsed_url.query)
                    if oig_id_match:
                        unique_identifier = f"OIG{oig_id_match.group(1)}"
                    else:
                        unique_identifier = url
                else:
                    unique_identifier = url

                if unique_identifier not in seen_base_urls:
                    processed_urls.append(url)
                    seen_base_urls.add(unique_identifier)
            
            if len(processed_urls) > 0:
                self.__log(
                    f"{self.log.GREEN}Ditemukan {len(processed_urls)} gambar. Total waktu: {round(time.time() - start_time, 2)}s."
                )
                return processed_urls
            else:
                self.__log(f"{self.log.YELLOW}Ditemukan {len(processed_urls)} gambar (kurang dari 4 yang diharapkan atau masih ada gambar rendering/placeholder). Menunggu lagi...")

            await asyncio.sleep(3)
