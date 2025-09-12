import json
import os
import urllib.parse
from types import SimpleNamespace
from typing import Dict, List, Optional, Union

import fake_useragent
import httpx
from bs4 import BeautifulSoup

from ..utils.logger import LoggerHandler


class PinterestClient:
    def __init__(self, cookies_file_path: str = "cookies/Pinterest.txt", logging_enabled: bool = True):
        self.all_cookies = self._parse_cookie_file(cookies_file_path)
        if not self.all_cookies:
            raise ValueError("File cookie kosong atau tidak valid.")

        self.domain = next((v.lstrip('.') for k, v in self._parse_cookie_domains(cookies_file_path).items() if 'pinterest.com' in v), "www.pinterest.com")
        self.base_url = f"https://{self.domain}"

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": fake_useragent.UserAgent().random,
        }

        self.client = httpx.AsyncClient(
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

    def _parse_cookie_domains(self, file_path: str) -> dict:
        domains = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) == 7 and not line.startswith("#"):
                    domains[parts[5]] = parts[0]
        return domains

    def __log(self, message: str, color: str = "GREEN"):
        if self.logging_enabled:
            color_attr = getattr(self.log, color.upper(), self.log.GREEN)
            self.log.print(f"{color_attr}{message}")
            
    def _find_resource_response(self, data: Union[Dict, List]) -> Optional[List]:
        if isinstance(data, dict):
            if "resourceResponses" in data and isinstance(data["resourceResponses"], list):
                return data["resourceResponses"]
            for value in data.values():
                found = self._find_resource_response(value)
                if found:
                    return found
        elif isinstance(data, list):
            for item in data:
                found = self._find_resource_response(item)
                if found:
                    return found
        return None

    def _extract_pins_from_state(self, json_data: dict, limit: int) -> List[SimpleNamespace]:
        results = []
        try:
            resource_responses = self._find_resource_response(json_data)
            if not resource_responses:
                self.__log("Kunci 'resourceResponses' tidak ditemukan dalam JSON.", color="YELLOW")
                return []

            pins_data = resource_responses[0].get("response", {}).get("data", {})
            pins_list = pins_data.get("results", [])

            for pin_data in pins_list[:limit]:
                if not isinstance(pin_data, dict) or pin_data.get("type") != "pin":
                    continue
                images = pin_data.get("images", {})
                if not images:
                    continue

                image_url = images.get("orig", {}).get("url") or next((v['url'] for v in images.values() if isinstance(v, dict) and 'url' in v), None)
                if not image_url:
                    continue

                pin_id = pin_data.get("id", "")
                results.append(SimpleNamespace(
                    id=pin_id,
                    image_url=image_url,
                    description=pin_data.get("description", "") or pin_data.get("grid_title", ""),
                    url=f"{self.base_url}/pin/{pin_id}/" if pin_id else self.base_url
                ))
        except (KeyError, IndexError, TypeError) as e:
            self.__log(f"Gagal mem-parsing data pin: {e}", color="YELLOW")
        return results

    async def _fetch_and_extract_from_html(self, url: str, limit: int) -> List[SimpleNamespace]:
        try:
            full_url = f"{self.base_url}{url}"
            response = await self.client.get(full_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            script_tags = soup.find_all("script")
            for tag in script_tags:
                if tag.string and "resourceResponses" in tag.string:
                    try:
                        json_data = json.loads(tag.string)
                        return self._extract_pins_from_state(json_data, limit)
                    except json.JSONDecodeError:
                        continue

            raise Exception("Gagal menemukan atau mem-parsing JSON yang berisi data pin di halaman HTML.")

        except httpx.HTTPStatusError as e:
            raise Exception(f"Pinterest merespons dengan error {e.response.status_code}. Pastikan cookie Anda valid.")
        except Exception as e:
            raise e

    async def search_pins(self, query: str, limit: int = 10) -> List[SimpleNamespace]:
        if not query:
            raise ValueError("Query tidak boleh kosong.")

        self.__log(f"Mencari pin untuk: '{query}' di '{self.base_url}'")
        search_path = f"/search/pins/?q={urllib.parse.quote(query)}&rs=typed"
        pins = await self._fetch_and_extract_from_html(search_path, limit)
        self.__log(f"Menemukan {len(pins)} pin untuk query '{query}'.")
        return pins

    async def get_user_pins(self, username: str, limit: int = 10) -> List[SimpleNamespace]:
        clean_username = username.lstrip('@')
        self.__log(f"Mengambil pin pengguna untuk: '{clean_username}'")
        profile_path = f"/{clean_username}/_created/"
        pins = await self._fetch_and_extract_from_html(profile_path, limit)
        self.__log(f"Menemukan {len(pins)} pin untuk pengguna '{clean_username}'.")
        return pins
