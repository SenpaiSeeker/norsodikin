import json
import os
import urllib.parse
from types import SimpleNamespace
from typing import List

import fake_useragent
import httpx

from ..utils.logger import LoggerHandler


class PinterestClient:
    def __init__(self, cookies_file_path: str = "pinterest.txt", logging_enabled: bool = True):
        self.all_cookies = self._parse_cookie_file(cookies_file_path)
        self.base_url = "https://www.pinterest.com"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            cookies=self.all_cookies,
            headers={
                "User-Agent": fake_useragent.UserAgent().random,
                "Accept": "application/json, text/javascript, */*, q=0.01",
                "Accept-Language": "en-US,en;q=0.5",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": self.base_url,
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

    async def _call_api(self, resource_name: str, source_url: str, data_payload: dict):
        data_json = json.dumps(data_payload)
        api_url = f"/resource/{resource_name}/get/?source_url={urllib.parse.quote(source_url)}&data={urllib.parse.quote(data_json)}"

        try:
            response = await self.client.get(api_url)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise Exception(f"Gagal mengambil data dari API Pinterest: {e}")
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

                image_versions = pin_data.get("images", {})
                if not image_versions:
                    continue

                image_url = (
                    image_versions.get("originals", {}).get("url")
                    or image_versions.get("736x", {}).get("url")
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
        source_url = f"/search/pins/?q={urllib.parse.quote(query)}&rs=typed"
        data_payload = {"options": {"q": query, "scope": "pins"}, "context": {}}

        json_data = await self._call_api("BaseSearchResource", source_url, data_payload)
        pins = self._extract_pins_from_json(json_data, limit)

        self.__log(f"Menemukan {len(pins)} pin untuk query '{query}'.")
        return pins

    async def get_user_pins(self, username: str, limit: int = 10) -> List[SimpleNamespace]:
        if not username:
            raise ValueError("Username tidak boleh kosong.")
        
        clean_username = username.lstrip('@')
        self.__log(f"Mengambil pin untuk pengguna: '{clean_username}'")
        source_url = f"/{clean_username}/_created/"
        data_payload = {"options": {"username": clean_username}, "context": {}}

        json_data = await self._call_api("UserResource", source_url, data_payload)
        pins = self._extract_pins_from_json(json_data, limit)

        self.__log(f"Menemukan {len(pins)} pin untuk pengguna '{clean_username}'.")
        return pins
