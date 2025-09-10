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
            cookies={"_U": auth_cookie_u} if auth_cookie_u else {},
            headers={
                "User-Agent": fake_useragent.UserAgent().random if hasattr(fake_useragent, "UserAgent") else "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
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

    def _parse_cookie_file(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Cookie file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.strip().startswith("#") or line.strip() == "":
                    continue

                parts = line.strip().split("\t")
                if len(parts) >= 7 and "bing.com" in parts[0] and parts[5] == "_U":
                    return parts[6]

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
            m = re.search(r"_U=([^; \n]+)", text)
            if m:
                return m.group(1)

        raise ValueError(f"Could not find the '_U' cookie for bing.com in {file_path}")

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    def _clean_url(self, u: str) -> str:
        if u.startswith("/"):
            u = f"{self.base_url}{u}"
        parsed = urllib.parse.urlsplit(u)
        if not parsed.scheme:
            u = f"{self.base_url}{u}"
            parsed = urllib.parse.urlsplit(u)
        qs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        filtered = [(k, v) for (k, v) in qs if k.lower() not in ("w", "width", "h", "height", "s", "size")]
        new_q = urllib.parse.urlencode(filtered, doseq=True)
        rebuilt = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_q, parsed.fragment))
        return rebuilt

    async def generate(self, prompt: str, max_wait_seconds: int = 300):
        if not prompt:
            raise ValueError("Prompt tidak boleh kosong.")

        start_time = time.time()
        self.__log(f"{self.log.GREEN}Memulai pembuatan gambar untuk prompt: '{prompt}'")
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"/images/create?q={encoded_prompt}&rt=4&FORM=GENCRE"

        try:
            response = await self.client.post(url, data={"q": prompt})
        except httpx.RequestError as e:
            raise Exception(f"Gagal mengirim permintaan pembuatan gambar: {e}")

        if response.status_code not in (200, 302, 303):
            self.__log(f"{self.log.RED}Status code tidak valid: {response.status_code}. Mungkin cookie tidak valid.")
            self.__log(f"{self.log.RED}Response: {response.text[:250]}...")
            raise Exception("Permintaan gagal. Pastikan cookie _U valid dan tidak kadaluarsa.")

        redirect_url = response.headers.get("Location") or response.headers.get("location")
        request_id = None
        if redirect_url and "id=" in redirect_url:
            m = re.search(r"[?&](?:id|requestId|request_id)=([^&]+)", redirect_url)
            if m:
                request_id = m.group(1)

        if not request_id:
            m = re.search(r'"(?:id|requestId|request_id)"\s*:\s*"([^"]+)"', response.text)
            if m:
                request_id = m.group(1)

        if not request_id:
            m = re.search(r'window\.location\.href\s*=\s*["\']([^"\']+)["\']', response.text)
            if m:
                loc = m.group(1)
                mm = re.search(r"[?&](?:id|requestId|request_id)=([^&]+)", loc)
                if mm:
                    request_id = mm.group(1)

        if not request_id:
            m = re.search(r"\bid=([A-Za-z0-9\-_]+)\b", response.text)
            if m:
                request_id = m.group(1)

        if not request_id:
            raise Exception("Gagal mendapatkan ID permintaan dari redirect. Prompt mungkin diblokir.")

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

            if "errorMessage" in poll_response.text or "gil_err_msg" in poll_response.text:
                error_message = re.search(r'<div id="gil_err_msg">([^<]+)</div>', poll_response.text)
                if error_message:
                    raise Exception(f"Bing error: {error_message.group(1)}")
                try:
                    j = poll_response.json()
                    for k in ("error", "message", "errorMessage"):
                        if k in j:
                            raise Exception(f"Bing error: {j[k]}")
                except Exception:
                    pass

            image_urls = re.findall(r'src="([^"]+)"', poll_response.text)
            image_urls += re.findall(r"src='([^']+)'", poll_response.text)
            image_urls += re.findall(r'"(https?://[^"]+\.(?:jpe?g|png|webp)[^"]*)"', poll_response.text)
            processed_urls = []
            seen = set()
            for u in image_urls:
                if "thfvnext" not in u and not re.search(r"\.(?:png|jpg|jpeg|webp)", u):
                    continue
                try:
                    cleaned = self._clean_url(u)
                except Exception:
                    cleaned = u
                if cleaned not in seen:
                    seen.add(cleaned)
                    processed_urls.append(cleaned)

            if processed_urls:
                self.__log(
                    f"{self.log.GREEN}Ditemukan {len(processed_urls)} gambar. Total waktu: {round(time.time() - start_time, 2)}s."
                )
                return processed_urls

            await asyncio.sleep(3)

    def generate_sync(self, prompt: str, max_wait_seconds: int = 300):
        return asyncio.get_event_loop().run_until_complete(self.generate(prompt, max_wait_seconds))
