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
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": f"{self.base_url}/images/create",
                "Content-Type": "application/json",
                "Origin": self.base_url,
                "DNT": "1",
                "Connection": "keep-alive",
            },
            follow_redirects=True,
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
        self.__log(f"{self.log.GREEN}Memulai pembuatan gambar GPT-4.0 untuk prompt: '{prompt}'")

        url = "/images/create"
        payload = {"prompt": prompt, "gptVersion": "4.0"}
        try:
            response = await self.client.post(url, json=payload)
        except httpx.RequestError as e:
            raise Exception(f"Gagal mengirim permintaan pembuatan gambar: {e}")

        if response.status_code not in (200, 202):
            self.__log(f"{self.log.RED}Status code tidak valid: {response.status_code}")
            self.__log(f"{self.log.RED}Response: {response.text[:250]}...")
            raise Exception("Permintaan gagal. Pastikan cookie _U valid dan tidak kadaluarsa.")

        data = response.json()
        request_id = data.get("id")
        if not request_id:
            raise Exception("Gagal mendapatkan ID permintaan dari response.")

        self.__log(f"{self.log.GREEN}Permintaan berhasil dikirim. ID: {request_id}")
        polling_url = f"/images/create/async/results/{request_id}"
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

            result_data = poll_response.json()
            if "error" in result_data:
                raise Exception(f"Bing error: {result_data['error']}")

            image_urls = result_data.get("images", [])
            if image_urls:
                self.__log(
                    f"{self.log.GREEN}Ditemukan {len(image_urls)} gambar. Total waktu: {round(time.time() - start_time, 2)}s."
                )
                return image_urls

            await asyncio.sleep(3)
