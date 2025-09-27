import asyncio
import os
import re
from types import SimpleNamespace
from http.cookiejar import MozillaCookieJar

import httpx

from ..utils.logger import LoggerHandler
from ..utils.shell import ShellExecutor

class ViuDownloader:
    def __init__(self, cookies_file: str = "cookies.txt"):
        if not os.path.exists(cookies_file):
            raise FileNotFoundError(f"Cookies file not found at: {cookies_file}")

        self.cookies_file = cookies_file
        self.log = LoggerHandler()
        self.shell = ShellExecutor()
        
        cookie_jar = MozillaCookieJar(self.cookies_file)
        cookie_jar.load(ignore_discard=True, ignore_expires=True)

        self.token = None
        for cookie in cookie_jar:
            if cookie.name == 'token':
                self.token = cookie.value
                break
        
        if not self.token:
            raise ValueError(f"Required 'token' cookie not found in the cookies file: {self.cookies_file}")

        self.session = httpx.AsyncClient(
            cookies=cookie_jar,
            headers={
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                'accept-language': 'en-US,en;q=0.9,id;q=0.8',
            },
            timeout=30.0,
            follow_redirects=True
        )
        self.api_headers = {
            "authorization": f"Bearer {self.token}",
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'accept-language': 'en-US,en;q=0.9,id;q=0.8',
            'origin': 'https://www.viu.com',
            'referer': 'https://www.viu.com/',
        }

    async def _api_request(self, endpoint, params):
        base_url = "https://api-gateway-global.viu.com/api/mobile"
        default_params = {
            "platform_flag_label": "web",
            "area_id": "1001",
            "language_flag_id": "3",
            "countryCode": "ID",
            "ut": "0",
            "os_flag_id": "1"
        }
        all_params = {**default_params, **params}
        try:
            response = await self.session.get(base_url, headers=self.api_headers, params=all_params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            self.log.error(f"VIU API Error for endpoint {endpoint}: {e.response.status_code} - {e.response.text}")
            raise Exception(f"VIU API returned status {e.response.status_code}")
        except Exception as e:
            self.log.error(f"Error during VIU API request to {endpoint}: {e}")
            raise e

    def _extract_product_id_from_url(self, url: str):
        match = re.search(r'viu\.com/.*?/vod/(\d+)', url)
        return match.group(1) if match else None

    async def get_episode_details(self, episode_url: str) -> SimpleNamespace:
        product_id = self._extract_product_id_from_url(episode_url)
        if not product_id:
            raise ValueError("Could not extract a valid Product ID from the URL.")

        details_data = await self._api_request("/vod/detail", {"product_id": product_id})
        product_info = details_data.get("data", {}).get("current_product", {})
        
        series_name = product_info.get("series_name", "Unknown Series")
        episode_name = product_info.get("name", "Unknown Episode")
        full_name = f"{series_name} - {episode_name}".strip(" - ")

        subtitles = [
            SimpleNamespace(lang=sub.get("name"), url=sub.get("subtitle_url"))
            for sub in details_data.get("data", {}).get("product_subtitle", [])
        ]

        playback_data = await self._api_request("/playback/distribute", {"ccs_product_id": product_info.get("ccs_product_id")})
        stream_urls = playback_data.get("data", {}).get("stream", {}).get("url", {})
        
        resolutions = {
            "240p": stream_urls.get("s240p"),
            "480p": stream_urls.get("s480p"),
            "720p": stream_urls.get("s720p"),
            "1080p": stream_urls.get("s1080p"),
        }
        
        return SimpleNamespace(
            product_id=product_id,
            ccs_product_id=product_info.get("ccs_product_id"),
            full_name=full_name,
            subtitles=subtitles,
            resolutions={k: v for k, v in resolutions.items() if v}
        )
        
    async def download(
        self,
        episode_url: str,
        resolution: str = "720p",
        subtitle_lang: str = "Bahasa Indonesia",
        output_dir: str = "downloads/viu"
    ) -> str:
        
        os.makedirs(output_dir, exist_ok=True)
        details = await self.get_episode_details(episode_url)

        manifest_url = details.resolutions.get(resolution.lower())
        if not manifest_url:
            available_res = ", ".join(details.resolutions.keys())
            raise ValueError(f"Resolution '{resolution}' not found. Available: {available_res}")

        subtitle_path = None
        subtitle_url = next((sub.url for sub in details.subtitles if sub.lang == subtitle_lang), None)
        if subtitle_url:
            subtitle_filename = f"{details.full_name}.srt"
            subtitle_path = os.path.join(output_dir, subtitle_filename)
            response = await self.session.get(subtitle_url)
            with open(subtitle_path, "wb") as f:
                f.write(response.content)
            self.log.info(f"Subtitle '{subtitle_lang}' downloaded to {subtitle_path}")

        video_filename_base = os.path.join(output_dir, details.full_name)
        hls_command = (
            f'N_m3u8DL-RE "{manifest_url}" '
            f'--save-name "{video_filename_base}" '
            f'--tmp-dir "{output_dir}/temp" '
            f'--save-dir "{output_dir}" '
            f"-M format=mp4 --thread-count 16 -mt"
        )
        
        self.log.info("Starting HLS video download...")
        stdout, stderr, code = await self.shell.run(hls_command)
        if code != 0:
            raise Exception(f"N_m3u8DL-RE failed with exit code {code}:\n{stderr}")
        
        downloaded_video_path = f"{video_filename_base}.mp4"
        self.log.info(f"Video downloaded to: {downloaded_video_path}")

        if not subtitle_path:
            return downloaded_video_path

        self.log.info("Merging video and subtitles...")
        merged_video_path = f"{video_filename_base} [Merged].mp4"
        
        escaped_subtitle_path = subtitle_path.replace("\\", "/").replace(":", "\\:")
        
        ffmpeg_command = (
            f'ffmpeg -y -i "{downloaded_video_path}" '
            f"-vf \"subtitles='{escaped_subtitle_path}':force_style='Fontsize=24,PrimaryColour=&Hffffff&'\" "
            f'-c:a copy -c:v libx264 -preset veryfast "{merged_video_path}"'
        )
        
        stdout, stderr, code = await self.shell.run(ffmpeg_command)
        if code != 0:
            self.log.error(f"FFmpeg merge failed. Returning unmerged video. Error:\n{stderr}")
            return downloaded_video_path

        os.remove(downloaded_video_path)
        os.remove(subtitle_path)
        
        self.log.info(f"Successfully merged. Final file: {merged_video_path}")
        return merged_video_path
