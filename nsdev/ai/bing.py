import asyncio
import os
import re
import time
import urllib.parse
from typing import List, Optional

import fake_useragent
import httpx

from ..utils.logger import LoggerHandler


class ImageGenerator:
    def __init__(self, cookies_file_path: str = "cookies.txt", logging_enabled: bool = True):
        self.base_url = "https://www.bing.com"
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()
        self._auth_cookie = self._parse_cookie_file(cookies_file_path)
        ua = fake_useragent.UserAgent().random
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "User-Agent": ua,
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
            cookies={"_U": self._auth_cookie},
            follow_redirects=False,
            timeout=200,
        )

    def _parse_cookie_file(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Cookie file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue
                if "\t" in raw:
                    parts = raw.split("\t")
                    if len(parts) >= 7:
                        domain = parts[0]
                        name = parts[5]
                        value = parts[6]
                        if name == "_U" and ("bing.com" in domain or domain.endswith("bing.com")):
                            return value
                if "=" in raw:
                    if raw.startswith("_U="):
                        return raw.split("=", 1)[1]
                    try:
                        kv = dict(part.split("=", 1) for part in raw.split(";") if "=" in part)
                        if "_U" in kv:
                            return kv["_U"]
                    except Exception:
                        pass
        raise ValueError(f"Could not find the '_U' cookie for bing.com in {file_path}")

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def _extract_request_id_from_redirect(self, response: httpx.Response) -> Optional[str]:
        loc = response.headers.get("Location")
        if not loc:
            return None
        m = re.search(r"(?:requestId|id)=([^&\\n]+)", loc)
        if m:
            return m.group(1)
        return None

    async def _extract_request_id_from_html(self, html: str) -> Optional[str]:
        patterns = [
            r"requestId[\"']?\s*[:=]\s*[\"']?([0-9a-fA-F\-]{8,})[\"']?",
            r"id=([0-9a-fA-F\-]{8,})",
            r"data-request-id=[\"']([^\"']+)[\"']",
        ]
        for p in patterns:
            m = re.search(p, html)
            if m:
                return m.group(1)
        return None

    async def _extract_images_from_json(self, j: dict) -> List[str]:
        urls: List[str] = []
        if not isinstance(j, dict):
            return urls

        def add(u: Optional[str]):
            if not u:
                return
            u = u.split("?w=")[0]
            if u not in urls:
                urls.append(u)

        if "images" in j and isinstance(j["images"], list):
            for it in j["images"]:
                if isinstance(it, dict):
                    add(it.get("url") or it.get("src"))
                elif isinstance(it, str):
                    add(it)
        if "result" in j and isinstance(j["result"], dict):
            r = j["result"]
            if "images" in r and isinstance(r["images"], list):
                for it in r["images"]:
                    if isinstance(it, dict):
                        add(it.get("src") or it.get("url"))

        def walk(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)
            elif isinstance(obj, str):
                if obj.startswith("http") and "bing.com" in obj and "OIG" in obj:
                    add(obj)

        walk(j)
        return urls

    async def generate(self, prompt: str, max_wait_seconds: int = 300, poll_interval: float = 3.0) -> List[str]:
        if not prompt:
            raise ValueError("Prompt tidak boleh kosong.")
        start_time = time.time()
        self.__log(f"{self.log.GREEN}Memulai pembuatan gambar untuk prompt: '{prompt}'")
        encoded_prompt = urllib.parse.quote(prompt)
        post_url = f"/images/create?q={encoded_prompt}&rt=4&FORM=GENCRE"
        try:
            response = await self.client.post(post_url)
        except httpx.RequestError as e:
            raise Exception(f"Gagal mengirim permintaan pembuatan gambar: {e}")
        request_id: Optional[str] = None
        if response.status_code == 302:
            request_id = await self._extract_request_id_from_redirect(response)
        elif response.status_code in (200, 201, 202):
            j = None
            try:
                j = response.json()
            except Exception:
                j = None
            if isinstance(j, dict):
                request_id = j.get("requestId") or j.get("id")
                if not request_id:
                    imgs = await self._extract_images_from_json(j)
                    if imgs:
                        self.__log(
                            f"{self.log.GREEN}Ditemukan {len(imgs)} gambar langsung dari respons JSON. Total waktu: {round(time.time() - start_time, 2)}s."
                        )
                        return imgs
            if not request_id:
                html = response.text
                request_id = await self._extract_request_id_from_html(html)
                if not request_id:
                    images = re.findall(r'src="([^\"]+)"', html)
                    processed = []
                    for u in images:
                        if isinstance(u, str) and "bing.com" in u and "OIG" in u:
                            processed.append(u.split("?")[0])
                    processed = list(dict.fromkeys(processed))
                    if processed:
                        self.__log(
                            f"{self.log.GREEN}Ditemukan {len(processed)} gambar langsung dari HTML. Total waktu: {round(time.time() - start_time, 2)}s."
                        )
                        return processed
        else:
            raise Exception("Permintaan gagal. Pastikan cookie _U valid dan tidak kadaluarsa.")
        if not request_id:
            raise Exception(
                "Gagal mendapatkan ID permintaan dari respons. Prompt mungkin diblokir atau format respons baru belum dikenali."
            )
        self.__log(f"{self.log.GREEN}Permintaan berhasil dikirim. ID: {request_id}")
        polling_url = f"/images/create/async/results/{request_id}?q={encoded_prompt}"
        self.__log(f"{self.log.GREEN}Menunggu hasil gambar...")
        wait_start_time = time.time()
        max_attempts = max(1, int(max_wait_seconds / max(poll_interval, 0.1)))
        attempts = 0
        while True:
            if time.time() - wait_start_time > max_wait_seconds:
                raise Exception(f"Waktu tunggu habis ({max_wait_seconds} detik).")
            attempts += 1
            if attempts > max_attempts * 2:
                raise Exception("Polling gagal setelah banyak percobaan.")
            try:
                poll_response = await self.client.get(polling_url)
            except httpx.RequestError as e:
                self.__log(f"{self.log.YELLOW}Gagal polling, mencoba lagi... Error: {e}")
                await asyncio.sleep(min(poll_interval, 5))
                continue
            if poll_response.status_code in (202, 204):
                await asyncio.sleep(poll_interval)
                continue
            if poll_response.status_code != 200:
                await asyncio.sleep(poll_interval)
                continue
            text = poll_response.text
            if "errorMessage" in text or "gil_err_msg" in text:
                err = re.search(r'<div[^>]*id=["\']gil_err_msg["\'][^>]*>([^<]+)</div>', text)
                if err:
                    raise Exception(f"Bing error: {err.group(1)}")
                raise Exception("Bing error saat memproses permintaan.")
            j = None
            try:
                j = poll_response.json()
            except Exception:
                j = None
            if isinstance(j, dict):
                imgs = await self._extract_images_from_json(j)
                if imgs:
                    self.__log(
                        f"{self.log.GREEN}Ditemukan {len(imgs)} gambar. Total waktu: {round(time.time() - start_time, 2)}s."
                    )
                    return imgs
            images = re.findall(r'src="([^\"]+)"', text)
            processed_urls = []
            for u in images:
                if isinstance(u, str) and "bing.com" in u and "OIG" in u:
                    processed_urls.append(u.split("?")[0])
            processed_urls = list(dict.fromkeys(processed_urls))
            if processed_urls:
                self.__log(
                    f"{self.log.GREEN}Ditemukan {len(processed_urls)} gambar. Total waktu: {round(time.time() - start_time, 2)}s."
                )
                return processed_urls
            await asyncio.sleep(poll_interval)
