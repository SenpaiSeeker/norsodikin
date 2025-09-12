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
    def __init__(self, cookies_file_path: str = "pinterest.txt", logging_enabled: bool = True):
        self.all_cookies = self._parse_cookie_file(cookies_file_path)
        self.csrf_token = self.all_cookies.get("csrftoken")
        self.app_version = None

        if not self.csrf_token:
            raise ValueError(
                "File cookie tidak memiliki 'csrftoken'. Pastikan Anda login dan mengekspor cookie dengan benar."
            )

        self.base_url = "https://www.pinterest.com"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            cookies=self.all_cookies,
            headers={"User-Agent": fake_useragent.UserAgent().random},
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
                    cookies_dict[parts[5]] = parts[6]
        return cookies_dict

    def __log(self, message: str, color: str = "GREEN"):
        if self.logging_enabled:
            color_attr = getattr(self.log, color.upper(), self.log.GREEN)
            self.log.print(f"{color_attr}{message}")

    async def _ensure_app_version(self):
        if self.app_version:
            return
        try:
            self.__log("Mengambil versi aplikasi Pinterest...", color="YELLOW")
            response = await self.client.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            script_tag = soup.find("script", {"id": "initial-state"})
            if not script_tag:
                raise Exception("Tidak dapat menemukan JSON state awal untuk mengambil app version.")
            initial_data = json.loads(script_tag.string)
            self.app_version = initial_data.get("context", {}).get("appVersion")
            if not self.app_version:
                raise Exception("Key 'appVersion' tidak ditemukan dalam JSON state awal.")
            self.__log(f"Berhasil mendapatkan App Version: {self.app_version}")
        except Exception as e:
            raise Exception(f"Gagal mengambil App Version dinamis dari Pinterest: {e}")

    async def _call_api(self, resource_name: str, source_url: str, data_payload: dict):
        await self._ensure_app_version()

        data_json = json.dumps(data_payload)
        api_url = f"/resource/{resource_name}/get/?source_url={urllib.parse.quote(source_url)}&data={urllib.parse.quote(data_json)}"

        headers = {
            "Accept": "application/json, text/javascript, */*, q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": self.csrf_token,
            "X-App-Version": self.app_version,
            "Referer": f"{self.base_url}{source_url}",
        }

        try:
            response = await self.client.get(api_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_details = f"Server merespons dengan status {e.response.status_code}."
            if "authentication failed" in e.response.text.lower():
                error_details += " Otentikasi gagal, cookie mungkin tidak valid atau sudah kedaluwarsa."
            raise Exception(f"Gagal mengambil data dari API Pinterest: {error_details}")
        except json.JSONDecodeError:
            raise Exception("Gagal mem-parsing respons JSON dari API. Cookie mungkin tidak valid.")
        except Exception as e:
            raise e

    def _extract_pins_from_json(self, json_data, limit: int) -> List[SimpleNamespace]:
        results = []
        try:
            resource_response = json_data.get("resource_response", {})
            pins_data = resource_response.get("data", {})
            pins = pins_data.get("results", [])
            if not pins:
                pins = pins_data.get("data", [])

            for pin_data in pins[:limit]:
                if not isinstance(pin_data, dict) or pin_data.get("type") != "pin":
                    continue
                images = pin_data.get("images")
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
                results.append(SimpleNamespace(id=pin_id, url=pin_url, image_url=image_url, description=description))
        except (KeyError, IndexError, TypeError) as e:
            self.__log(f"Error saat parsing data pin: {e}", color="YELLOW")
        return results

    async def search_pins(self, query: str, limit: int = 10) -> List[SimpleNamespace]:
        if not query:
            raise ValueError("Query tidak boleh kosong.")

        self.__log(f"Mencari pin di Pinterest untuk: '{query}'")
        source_url = f"/search/pins/?q={urllib.parse.quote(query)}&rs=typed"
        data_payload = {"options": {"q": query, "scope": "pins"}, "context": {}}

        json_data = await self._call_api("BaseSearchResource", source_url, data_payload)
        pins = self._extract_pins_from_json(json_data, limit)
        self.__log(f"Menemukan {len(pins)} pin untuk query '{query}'.")
        return pins

    async def get_user_pins(self, username: str, limit: int = 10) -> List[SimpleNamespace]:
        if not username:
            raise ValueError("Username tidak boleh kosong.")

        clean_username = username.lstrip("@")
        self.__log(f"Mengambil pin untuk pengguna: '{clean_username}'")
        source_url = f"/{clean_username}/_created/"
        data_payload = {"options": {"username": clean_username}, "context": {}}

        json_data = await self._call_api("UserResource", source_url, data_payload)
        pins = self._extract_pins_from_json(json_data, limit)
        self.__log(f"Menemukan {len(pins)} pin untuk pengguna '{clean_username}'.")
        return pins
