import json
import os
import urllib.parse
from types import SimpleNamespace
from typing import List

import fake_useragent
import httpx

from ..utils.logger import LoggerHandler


class PinterestClient:
    def __init__(self, cookies_file_path: str = "cookies/Pinterest.txt", logging_enabled: bool = True):
        self.all_cookies = self._parse_cookie_file(cookies_file_path)
        self.csrf_token = self.all_cookies.get("csrftoken")
        if not self.csrf_token:
            raise ValueError(
                "File cookie tidak memiliki 'csrftoken'. Pastikan cookie diekspor dengan benar dari sesi yang sudah login."
            )

        self.base_url = "https://www.pinterest.com"
        self.api_url = f"{self.base_url}/resource/SearchResource/get/"
        self.user_api_url = f"{self.base_url}/resource/UserResource/get/"
        
        headers = {
            "Accept": "application/json, text/javascript, */*, q=0.01",
            "Accept-Language": "en-US,en;q=0.5",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": self.csrf_token,
            "User-Agent": fake_useragent.UserAgent().random,
        }

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            cookies=self.all_cookies,
            headers=headers,
            follow_redirects=True,
            timeout=30,
        )
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()

    def _parse_cookie_file(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File cookie tidak ditemukan di: {file_path}")
        cookies_dict = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) == 7 and not line.startswith("#"):
                    cookies_dict[parts[5]] = parts[6]
        return cookies_dict

    def __log(self, message: str, color: str = "GREEN"):
        if self.logging_enabled:
            color_attr = getattr(self.log, color.upper(), self.log.GREEN)
            self.log.print(f"{color_attr}{message}")

    def _extract_pins(self, json_data: dict, limit: int) -> List[SimpleNamespace]:
        results = []
        try:
            res_response = json_data.get("resource_response", {})
            pins_data = res_response.get("data", {})
            pins_list = pins_data.get("results", [])

            if not pins_list:
                self.__log("API mengembalikan data pin kosong. Query mungkin tidak menghasilkan apa-apa.", color="YELLOW")
                return []

            for pin in pins_list[:limit]:
                if not isinstance(pin, dict) or pin.get("type") != "pin":
                    continue
                images = pin.get("images", {})
                if not images:
                    continue
                
                image_url = images.get("orig", {}).get("url") or next((v['url'] for k, v in images.items() if 'url' in v), None)
                if not image_url:
                    continue

                results.append(SimpleNamespace(
                    id=pin.get("id", ""),
                    image_url=image_url,
                    description=pin.get("description", "") or pin.get("grid_title", ""),
                    url=f"{self.base_url}/pin/{pin.get('id', '')}/"
                ))
        except Exception as e:
            self.__log(f"Gagal mem-parsing data pin dari respons API: {e}", color="RED")
        return results

    async def search_pins(self, query: str, limit: int = 10, bookmarks: list = []) -> List[SimpleNamespace]:
        if not query:
            raise ValueError("Query tidak boleh kosong.")
        
        self.__log(f"Mencari pin melalui API untuk: '{query}'")
        source_url = f"/search/pins/?q={urllib.parse.quote(query)}&rs=typed"
        data = {
            "options": {
                "q": query,
                "scope": "pins",
                "bookmarks": bookmarks,
            },
            "context": {},
        }
        params = f"source_url={urllib.parse.quote(source_url)}&data={urllib.parse.quote(json.dumps(data))}"
        
        try:
            response = await self.client.get(f"{self.api_url}?{params}")
            response.raise_for_status()
            pins = self._extract_pins(response.json(), limit)
            self.__log(f"Menemukan {len(pins)} pin untuk query '{query}'.")
            return pins
        except httpx.HTTPStatusError as e:
            raise Exception(f"API Pinterest mengembalikan error {e.response.status_code}. Cookie Anda mungkin tidak valid atau sudah kedaluwarsa.")
        except Exception as e:
            raise Exception(f"Terjadi kesalahan saat memanggil API Pinterest: {e}")

    async def get_user_pins(self, username: str, limit: int = 10, bookmarks: list = []) -> List[SimpleNamespace]:
        clean_username = username.lstrip('@')
        self.__log(f"Mengambil pin pengguna melalui API untuk: '{clean_username}'")
        
        source_url = f"/{clean_username}/"
        data = {
            "options": {
                "username": clean_username,
                "bookmarks": bookmarks,
            },
            "context": {},
        }
        params = f"source_url={urllib.parse.quote(source_url)}&data={urllib.parse.quote(json.dumps(data))}"
        
        try:
            response = await self.client.get(f"{self.user_api_url}?{params}")
            response.raise_for_status()
            pins = self._extract_pins(response.json(), limit)
            self.__log(f"Menemukan {len(pins)} pin untuk pengguna '{clean_username}'.")
            return pins
        except httpx.HTTPStatusError as e:
            raise Exception(f"API Pinterest mengembalikan error {e.response.status_code}. Mungkin pengguna tidak ditemukan atau cookie Anda tidak valid.")
        except Exception as e:
            raise Exception(f"Terjadi kesalahan saat mengambil pin pengguna: {e}")
