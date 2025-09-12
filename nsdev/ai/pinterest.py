import json
import os
import urllib.parse
from types import SimpleNamespace
from typing import List

import fake_useragent
import httpx
from bs4 import BeautifulSoup

from ..utils.logger import LoggerHandler


class PinterestClient:
    def __init__(self, cookies_file_path: str = "cookies/Pinterest.txt", logging_enabled: bool = True):
        self.all_cookies = self._parse_cookie_file(cookies_file_path)
        if not self.all_cookies:
            raise ValueError("File cookie kosong atau tidak valid.")

        self.base_url = "https://www.pinterest.com"
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "max-age=0",
            "DNT": "1",
            "Sec-CH-UA": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Linux"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": fake_useragent.UserAgent().chrome,
        }

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            cookies=self.all_cookies,
            headers=self.headers,
            follow_redirects=True,
            timeout=30,
        )
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()

    def _parse_cookie_file(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"File cookie tidak ditemukan: {file_path}. Sediakan file cookie Netscape yang valid."
            )
        cookies_dict = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) == 7:
                    cookies_dict[parts[5]] = parts[6]
        return cookies_dict

    def __log(self, message: str, color: str = "GREEN"):
        if self.logging_enabled:
            color_attr = getattr(self.log, color.upper(), self.log.GREEN)
            self.log.print(f"{color_attr}{message}")

    def _extract_pins_from_initial_state(self, data: dict, limit: int) -> List[SimpleNamespace]:
        results = []
        try:
            initial_state = data.get("props", {}).get("initialReduxState", {})
            res_responses = initial_state.get("resourceResponses", [])
            if not res_responses:
                return []

            pins_data = res_responses[0].get("response", {}).get("data", {})
            pins_list = pins_data.get("results", [])
            if not pins_list:
                pins_list = pins_data.get("data", [])

            for pin_data in pins_list[:limit]:
                if not isinstance(pin_data, dict) or pin_data.get("type") != "pin":
                    continue
                images = pin_data.get("images", {})
                if not images:
                    continue
                image_url = (
                    images.get("orig", {}).get("url")
                    or images.get("736x", {}).get("url")
                    or (list(images.values())[0].get("url") if images else None)
                )
                if not image_url:
                    continue
                pin_id = pin_data.get("id", "")
                description = pin_data.get("description", "") or pin_data.get("grid_title", "")
                pin_url = f"{self.base_url}/pin/{pin_id}/" if pin_id else self.base_url
                results.append(
                    SimpleNamespace(id=pin_id, url=pin_url, image_url=image_url, description=description)
                )
        except (KeyError, IndexError, TypeError) as e:
            self.__log(f"Error saat mem-parsing data pin dari initial props: {e}", color="YELLOW")
        return results

    async def _fetch_and_extract_pins_from_html(self, url: str, limit: int) -> List[SimpleNamespace]:
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            
            script_tag = soup.find("script", {"data-test-id": "initial-props"})

            if not script_tag:
                if "login" in response.text.lower() or "log in" in response.text.lower():
                    raise Exception(
                        "Otentikasi Gagal: Halaman login terdeteksi. Pastikan file cookie Anda terbaru dan valid."
                    )
                raise Exception(
                    "Struktur Halaman Berubah: Tidak dapat menemukan data 'initial-props'. Pastikan cookie valid."
                )

            json_data = json.loads(script_tag.string)
            return self._extract_pins_from_initial_state(json_data, limit)
        except httpx.HTTPStatusError as e:
            raise Exception(f"Pinterest merespons dengan error {e.response.status_code}. Cookie mungkin kedaluwarsa.")
        except Exception as e:
            raise e

    async def search_pins(self, query: str, limit: int = 10) -> List[SimpleNamespace]:
        if not query:
            raise ValueError("Query tidak boleh kosong.")

        self.__log(f"Mencari pin di Pinterest untuk: '{query}'")
        search_url = f"/search/pins/?q={urllib.parse.quote(query)}&rs=typed"

        pins = await self._fetch_and_extract_pins_from_html(search_url, limit)
        self.__log(f"Menemukan {len(pins)} pin untuk query '{query}'.")
        return pins

    async def get_user_pins(self, username: str, limit: int = 10) -> List[SimpleNamespace]:
        if not username:
            raise ValueError("Username tidak boleh kosong.")

        clean_username = username.lstrip("@")
        self.__log(f"Mengambil pin untuk pengguna: '{clean_username}'")
        profile_url = f"/{clean_username}/_created/"

        pins = await self._fetch_and_extract_pins_from_html(profile_url, limit)
        self.__log(f"Menemukan {len(pins)} pin untuk pengguna '{clean_username}'.")
        return pins
