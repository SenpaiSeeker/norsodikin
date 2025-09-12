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
    def __init__(self, cookies_file_path: str = "pinterest_cookies.txt", logging_enabled: bool = True):
        self.all_cookies = self._parse_cookie_file(cookies_file_path)
        self.base_url = "https://www.pinterest.com"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            cookies=self.all_cookies,
            headers={
                "User-Agent": fake_useragent.UserAgent().random,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
            },
            follow_redirects=True,
            timeout=30,
        )
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()

    def _parse_cookie_file(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"File cookie tidak ditemukan: {file_path}. Sediakan file cookie Netscape yang valid untuk Pinterest."
            )

        cookies_dict = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split("\t")
                if len(parts) == 7:
                    cookie_name = parts[5]
                    cookie_value = parts[6]
                    cookies_dict[cookie_name] = cookie_value
        return cookies_dict

    def __log(self, message: str, color: str = "GREEN"):
        if self.logging_enabled:
            color_attr = getattr(self.log, color.upper(), self.log.GREEN)
            self.log.print(f"{color_attr}{message}")

    async def _fetch_and_parse_json(self, url: str):
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            script_tag = soup.find("script", {"id": "initial-state"})
            if not script_tag:
                raise Exception(
                    "Tidak dapat menemukan JSON state awal. Cookie mungkin tidak valid atau struktur halaman telah berubah."
                )
            return json.loads(script_tag.string)
        except httpx.RequestError as e:
            raise Exception(f"Gagal mengambil data dari Pinterest: {e}")
        except json.JSONDecodeError:
            raise Exception("Gagal mem-parsing data JSON dari halaman Pinterest.")
        except Exception as e:
            raise e

    def _extract_pins_from_json(self, json_data, limit: int) -> List[SimpleNamespace]:
        results = []
        try:
            pins_data = json_data.get("resourceResponses", [{}])[0].get("response", {}).get("data", {})
            pins = pins_data.get("results", [])
            if not pins:
                pins = pins_data.get("data", [])

            for pin_data in pins[:limit]:
                if not isinstance(pin_data, dict) or pin_data.get("type") != "pin":
                    continue

                image_versions = pin_data.get("images", {})
                if not image_versions:
                    continue

                image_url = (
                    image_versions.get("736x", {}).get("url")
                    or image_versions.get("originals", {}).get("url")
                    or (list(image_versions.values())[0].get("url") if image_versions else None)
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
            self.__log(f"Error saat parsing data pin: {e}", color="YELLOW")
        return results

    async def search_pins(self, query: str, limit: int = 10) -> List[SimpleNamespace]:
        if not query:
            raise ValueError("Query tidak boleh kosong.")

        self.__log(f"Mencari pin di Pinterest untuk: '{query}'")
        encoded_query = urllib.parse.quote(query)
        search_url = f"/search/pins/?q={encoded_query}&rs=typed"

        json_data = await self._fetch_and_parse_json(search_url)
        pins = self._extract_pins_from_json(json_data, limit)

        self.__log(f"Menemukan {len(pins)} pin untuk query '{query}'.")
        return pins

    async def get_user_pins(self, username: str, limit: int = 10) -> List[SimpleNamespace]:
        if not username:
            raise ValueError("Username tidak boleh kosong.")

        self.__log(f"Mengambil pin untuk pengguna: '{username}'")
        profile_url = f"/{username.lstrip('@')}/_created/"

        json_data = await self._fetch_and_parse_json(profile_url)
        pins = self._extract_pins_from_json(json_data, limit)

        self.__log(f"Menemukan {len(pins)} pin untuk pengguna '{username}'.")
        return pins
