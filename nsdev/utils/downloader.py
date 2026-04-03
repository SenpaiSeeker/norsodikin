import asyncio
import json
import os
import re
from functools import partial
from http.cookiejar import MozillaCookieJar
from types import SimpleNamespace
from typing import List, Optional
from urllib.parse import urlparse

import aiofiles
import httpx
import wget
from bs4 import BeautifulSoup
from faker import Faker
from yt_dlp import YoutubeDL

from ..data.ymlreder import YamlHandler


class MediaDownloader:
    def __init__(
        self,
        cookies_file_path: str = "cookies.txt",
        download_path: str = "downloads",
        proxy: Optional[str] = None,
        speed_limit: Optional[int] = None,
        max_parallel: int = 3,
    ):
        self.download_path = download_path
        self.cookies_file_path = cookies_file_path
        self.proxy = proxy
        self.speed_limit = speed_limit
        self.semaphore = asyncio.Semaphore(max_parallel)

        os.makedirs(self.download_path, exist_ok=True)

        self.convert = YamlHandler()
        self.fake = Faker("id_ID")

    def _sanitize_filename(self, name: str) -> str:
        name = re.sub(r'[\\/*?:"<>|]', "", name)
        return name.strip()

    def _is_supported_social(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return domain in (
            "www.instagram.com",
            "instagram.com",
            "instagr.am",
            "twitter.com",
            "www.twitter.com",
            "x.com",
            "www.x.com",
            "www.tiktok.com",
            "tiktok.com",
            "vt.tiktok.com",
        )

    def _is_youtube_url(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return domain in (
            "www.youtube.com",
            "youtube.com",
            "youtu.be",
            "m.youtube.com",
            "ymusicapp.com",
        )

    def _build_base_opts(self, progress_callback, loop):
        def _hook(d):
            if d["status"] == "downloading" and progress_callback:
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                if total:
                    asyncio.run_coroutine_threadsafe(
                        progress_callback(d["downloaded_bytes"], total),
                        loop,
                    )

        opts = {
            "outtmpl": os.path.join(
                self.download_path,
                "%(title).50s_%(id)s.%(ext)s",
            ),
            "restrictfilenames": True,
            "quiet": True,
            "no_warnings": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "noplaylist": True,
            "continuedl": True,
            "merge_output_format": "mkv",
            "user_agent": self.fake.user_agent(),
            "js_runtimes": {
                "node": {},
            },
            "remote_components": ["ejs:github"],
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "android", "web"],
                    "player_skip": ["webpage", "configs"],
                }
            },
        }

        if os.path.exists(self.cookies_file_path):
            opts["cookiefile"] = self.cookies_file_path

        if self.proxy:
            opts["proxy"] = self.proxy

        if self.speed_limit:
            opts["ratelimit"] = self.speed_limit

        if progress_callback:
            opts["progress_hooks"] = [_hook]

        return opts

    def _select_format(self, resolution: Optional[str], audio_only: bool):
        if audio_only:
            return "bestaudio/best"

        if resolution:
            return f"bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]"

        return "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]"

    def _get_referer_headers(self, url: str):
        parsed = urlparse(url)

        if parsed.netloc == "cloud.hownetwork.xyz" and parsed.path.endswith(".m3u8"):
            parts = parsed.path.strip("/").split("/")

            if len(parts) >= 2:
                base_path = f"/{parts[0]}/{parts[1]}"
            else:
                base_path = os.path.dirname(parsed.path)

            referer = f"{parsed.scheme}://{parsed.netloc}{base_path}"

            return {
                "Referer": referer,
                "Origin": f"{parsed.scheme}://{parsed.netloc}",
                "User-Agent": self.fake.user_agent(),
            }

        return None

    def _sync_download(
        self,
        url: str,
        resolution: Optional[str],
        audio_only: bool,
        progress_callback,
        loop,
    ):
        opts = self._build_base_opts(progress_callback, loop)
        opts["format"] = self._select_format(resolution, audio_only)

        headers = self._get_referer_headers(url)
        if headers:
            opts["http_headers"] = headers

        if audio_only:
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)

            filepath = ydl.prepare_filename(info)
            if audio_only:
                filepath = os.path.splitext(filepath)[0] + ".mp3"

            thumb_path = None
            thumb_url = info.get("thumbnail")

            if thumb_url:
                try:
                    safe_name = self._sanitize_filename(info.get("id", "thumb"))
                    thumb_file = os.path.join(self.download_path, f"{safe_name}_thumb.jpg")
                    wget.download(thumb_url, thumb_file)
                    thumb_path = thumb_file
                except Exception:
                    thumb_path = None

            result_obj = self.convert._convertToNamespace(info)
            result_obj.downloaded_path = filepath
            result_obj.thumbnail_path = thumb_path

            return result_obj

    def _get_httpx_cookies(self):
        cookies = httpx.Cookies()
        cookies.set("age_verified", "1", domain="www.dubbindo.site")
        cookies.set("is_adult", "1", domain="www.dubbindo.site")
        cookies.set("age_verified", "1", domain=".dubbindo.site")

        if self.cookies_file_path and os.path.exists(self.cookies_file_path):
            try:
                cj = MozillaCookieJar(self.cookies_file_path)
                cj.load(ignore_discard=True, ignore_expires=True)
                for cookie in cj:
                    cookies.set(cookie.name, cookie.value, domain=cookie.domain, path=cookie.path)
            except Exception:
                pass

        return cookies

    async def extract_viu_episodes(self, url: str) -> List[str]:
        headers = {
            "User-Agent": self.fake.user_agent(),
            "Referer": url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }

        async with httpx.AsyncClient(follow_redirects=True, headers=headers, timeout=30.0) as client:
            res = await client.get(url)
            res.raise_for_status()
            html = res.text

        soup = BeautifulSoup(html, "html.parser")
        episode_urls = []

        match = re.search(r"window\.__INITIAL_STATE__\s*=\s*({.*?});", html)
        if match:
            try:
                json.loads(match.group(1))
                vod_ids = re.findall(r'"product_id"\s*:\s*"(\d+)"', match.group(1))
                for vid in vod_ids:
                    ep_url = f"https://www.viu.com/ott/id/id/vod/{vid}/"
                    if ep_url not in episode_urls:
                        episode_urls.append(ep_url)
            except Exception:
                pass

        if not episode_urls:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/vod/" in href:
                    full_url = href if href.startswith("http") else f"https://www.viu.com{href}"
                    if full_url not in episode_urls:
                        episode_urls.append(full_url)

        if not episode_urls:
            episode_urls.append(url)

        return episode_urls

    async def _download_dubbindo(self, url: str, progress_callback):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }

        cookies = self._get_httpx_cookies()

        async with httpx.AsyncClient(follow_redirects=True, headers=headers, cookies=cookies, timeout=30.0) as client:
            res = await client.get(url)
            res.raise_for_status()
            html = res.text

        if "Please subscribe" in html or "Log In" in html:
            raise Exception(
                "Video eksklusif (Terkunci)! Anda harus memberikan cookies.txt dari akun yang sudah berlangganan/login ke Dubbindo."
            )

        soup = BeautifulSoup(html, "html.parser")

        meta_title = soup.find("meta", property="og:title")
        title = meta_title["content"] if meta_title else "Dubbindo_Video"
        title_clean = self._sanitize_filename(title)

        meta_desc = soup.find("meta", property="og:description")
        description = meta_desc["content"] if meta_desc else ""

        meta_thumb = soup.find("meta", property="og:image")
        thumb_url = meta_thumb["content"] if meta_thumb else None

        video_url = None
        meta_video = soup.find("meta", property="og:video")
        if meta_video:
            video_url = meta_video["content"]
        else:
            cari_mp4 = re.search(r'src=["\']([^"\']+\.mp4)["\']', html)
            if cari_mp4:
                video_url = cari_mp4.group(1)

        if not video_url:
            raise Exception(
                "Gagal menemukan tautan video MP4 langsung. Pastikan link video tersedia dan bukan link premium."
            )

        duration_sec = 0

        meta_duration = soup.find("meta", property="video:duration")
        if meta_duration and meta_duration.get("content", "").isdigit():
            duration_sec = int(meta_duration["content"])

        if duration_sec == 0:
            meta_itemprop = soup.find("meta", itemprop="duration")
            if meta_itemprop and meta_itemprop.get("content", "").startswith("PT"):
                content = meta_itemprop["content"]
                h_match = re.search(r"(\d+)H", content)
                m_match = re.search(r"(\d+)M", content)
                s_match = re.search(r"(\d+)S", content)
                h = int(h_match.group(1)) if h_match else 0
                m = int(m_match.group(1)) if m_match else 0
                s = int(s_match.group(1)) if s_match else 0
                duration_sec = h * 3600 + m * 60 + s

        if duration_sec == 0:
            match_js = re.search(r'(?:duration|video_duration)\s*[:=]\s*["\']?([0-9:]+)["\']?', html, re.IGNORECASE)
            if match_js:
                val = match_js.group(1)
                if val.isdigit():
                    duration_sec = int(val)
                elif ":" in val:
                    parts = val.split(":")
                    if len(parts) == 3:
                        duration_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    elif len(parts) == 2:
                        duration_sec = int(parts[0]) * 60 + int(parts[1])

        if duration_sec == 0:
            for tag in soup.find_all(["span", "div", "p", "time"]):
                class_name = " ".join(tag.get("class", [])).lower()
                if "duration" in class_name or "time" in class_name:
                    text_val = tag.get_text(strip=True)
                    if re.match(r"^([0-9]{1,2}:)?[0-9]{1,2}:[0-9]{2}$", text_val):
                        parts = text_val.split(":")
                        if len(parts) == 3:
                            duration_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                        elif len(parts) == 2:
                            duration_sec = int(parts[0]) * 60 + int(parts[1])
                        break

        vid_path = os.path.join(self.download_path, f"{title_clean}.mp4")
        thumb_path = None

        if thumb_url:
            thumb_path = os.path.join(self.download_path, f"{title_clean}_thumb.jpg")
            try:
                async with httpx.AsyncClient(
                    follow_redirects=True, headers=headers, cookies=cookies, timeout=30.0
                ) as client:
                    t_res = await client.get(thumb_url)
                    t_res.raise_for_status()
                    with open(thumb_path, "wb") as f:
                        f.write(t_res.content)
            except Exception:
                thumb_path = None

        async with httpx.AsyncClient(follow_redirects=True, headers=headers, cookies=cookies, timeout=60.0) as client:
            async with client.stream("GET", video_url) as stream:
                stream.raise_for_status()
                total_size = int(stream.headers.get("Content-Length", 0))
                downloaded = 0

                async with aiofiles.open(vid_path, "wb") as f:
                    async for chunk in stream.aiter_bytes(chunk_size=1024 * 1024):
                        await f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            if asyncio.iscoroutinefunction(progress_callback):
                                await progress_callback(downloaded, total_size)
                            else:
                                progress_callback(downloaded, total_size)

        result_obj = SimpleNamespace(
            id=title_clean,
            title=title,
            duration=duration_sec,
            description=description,
            downloaded_path=vid_path,
            thumbnail_path=thumb_path,
            url=video_url,
        )
        return result_obj

    async def download(
        self,
        url: str,
        resolution: Optional[str] = None,
        audio_only: bool = False,
        progress_callback=None,
    ):
        async with self.semaphore:
            if "dubbindo.site" in url:
                return await self._download_dubbindo(url, progress_callback)

            loop = asyncio.get_running_loop()
            func = partial(
                self._sync_download,
                url,
                resolution,
                audio_only,
                progress_callback,
                loop,
            )
            return await loop.run_in_executor(None, func)

    async def download_batch(
        self,
        urls: List[str],
        resolution: Optional[str] = None,
        audio_only: bool = False,
    ):
        tasks = [self.download(url, resolution, audio_only) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def download_social(
        self,
        url: str,
        resolution: Optional[str] = None,
        audio_only: bool = False,
        progress_callback=None,
    ):
        if not self._is_supported_social(url):
            raise Exception("URL tidak didukung untuk social media")

        return await self.download(
            url,
            resolution=resolution,
            audio_only=audio_only,
            progress_callback=progress_callback,
        )

    async def search_youtube(self, query: str, limit: int = 10):
        loop = asyncio.get_running_loop()

        def _search():
            opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "extract_flat": "in_playlist",
                "nocheckcertificate": True,
                "geo_bypass": True,
                "extractor_args": {
                    "youtube": {
                        "player_client": ["ios", "android", "web"],
                        "player_skip": ["webpage", "configs"],
                    }
                },
            }
            if self.cookies_file_path and os.path.exists(self.cookies_file_path):
                opts["cookiefile"] = self.cookies_file_path

            is_youtube_url = self._is_youtube_url(query)
            if is_youtube_url:
                opts.update(
                    {
                        "noplaylist": False,
                        "extract_flat": True,
                    }
                )
            else:
                opts["default_search"] = f"ytsearch{limit}"

            with YoutubeDL(opts) as ydl:
                result = ydl.extract_info(query, download=False, process=not is_youtube_url)
                entries = result.get("entries", [])

                if entries:
                    return [self.convert._convertToNamespace(e) for e in entries]
                else:
                    return [self.convert._convertToNamespace(result)]

        return await loop.run_in_executor(None, _search)
