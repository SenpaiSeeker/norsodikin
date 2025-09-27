import asyncio
import os
import re
import shutil
import tempfile
from http.cookiejar import MozillaCookieJar
from typing import Callable, Optional

import httpx

from ..utils.logger import LoggerHandler


class ViuDownloader:
    def __init__(self, token: str, cookies_path: str = "cookies.txt"):
        if not token:
            raise ValueError("VIU Bearer Token is required.")
        
        self.log = LoggerHandler()
        self._viu_api = self._VIU_API(token, cookies_path, self.log)
        self.output_dir = "downloads_viu"
        os.makedirs(self.output_dir, exist_ok=True)

    async def _run_command(self, command: list, log_prefix: str) -> bool:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_output = stderr.decode('utf-8', errors='ignore').strip()
            self.log.error(f"[{log_prefix}] Failed. Return code: {process.returncode}")
            self.log.error(f"[{log_prefix}] Stderr: {error_output}")
            return False
        
        self.log.info(f"[{log_prefix}] Command executed successfully.")
        return True

    async def download_episode(
        self,
        url: str,
        resolution: str = "720p",
        subtitle_lang: str = "Indonesian",
        progress_callback: Optional[Callable] = None
    ) -> Optional[str]:

        self.log.info(f"Starting download process for URL: {url}")
        
        try:
            metadata = await self._viu_api.get_product_series_id(url)
            if not metadata:
                self.log.error("Failed to extract metadata from URL.")
                return None
            
            product_id, series_id, series_name = metadata
            self.log.info(f"Found Series: '{series_name}', Product ID: {product_id}")

            temp_dir = tempfile.mkdtemp()
            subtitle_path = None
            
            subtitles = await self._viu_api.get_subtitle(product_id)
            target_subtitle = next((s for s in subtitles if subtitle_lang.lower() in s['name'].lower()), None)

            if target_subtitle:
                sub_filename = f"{series_name}.srt"
                subtitle_path = os.path.join(temp_dir, sub_filename)
                await self._viu_api.download_file_http(target_subtitle['url'], subtitle_path)
                self.log.info(f"Subtitle downloaded to: {subtitle_path}")
            else:
                self.log.warning(f"Subtitle '{subtitle_lang}' not found. Proceeding without subtitles.")

            ccs_product_id = await self._viu_api.get_ccs_product_id_for_single(product_id)
            if not ccs_product_id:
                self.log.error(f"Could not find CCS Product ID for Product ID {product_id}")
                return None

            manifests = await self._viu_api.get_manifest(ccs_product_id)
            if not manifests:
                self.log.error("Failed to retrieve video manifests.")
                return None

            manifest_url = manifests.get(resolution.upper())
            if not manifest_url:
                self.log.warning(f"Resolution '{resolution}' not found. Falling back to best available.")
                manifest_url = list(manifests.values())[-1]

            self.log.info(f"Selected manifest URL for download.")
            
            video_filename_template = series_name.replace(":", "").replace("?", "")
            
            dl_command = [
                "N_m3u8DL-RE",
                manifest_url,
                "--save-name", video_filename_template,
                "--save-dir", temp_dir,
                "--thread-count", "8",
                "-mt",
                "-M", "format=mp4",
                "--select-video", "BEST",
                "--select-audio", "BEST"
            ]
            
            self.log.info(f"Executing N_m3u8DL-RE...")
            if not await self._run_command(dl_command, "HLS-Download"):
                shutil.rmtree(temp_dir)
                return None
            
            downloaded_video_path = os.path.join(temp_dir, f"{video_filename_template}.mp4")
            if not os.path.exists(downloaded_video_path):
                 self.log.error(f"Downloaded video file not found at expected path: {downloaded_video_path}")
                 shutil.rmtree(temp_dir)
                 return None

            final_video_path = os.path.join(self.output_dir, f"{video_filename_template}.mp4")

            if subtitle_path:
                self.log.info("Merging video and subtitles...")
                merged_output_path = os.path.join(self.output_dir, f"{video_filename_template} [SUB].mp4")
                
                merge_command = [
                    "ffmpeg", "-y",
                    "-i", downloaded_video_path,
                    "-i", subtitle_path,
                    "-c", "copy",
                    "-c:s", "mov_text",
                    "-metadata:s:s:0", f"language={subtitle_lang[:3].lower()}",
                    "-metadata:s:s:0", f"title={subtitle_lang}",
                    merged_output_path
                ]
                
                if await self._run_command(merge_command, "FFmpeg-Merge"):
                    final_video_path = merged_output_path
                else:
                    self.log.warning("Subtitle merge failed. Moving the original video.")
                    shutil.move(downloaded_video_path, final_video_path)
            else:
                shutil.move(downloaded_video_path, final_video_path)

            shutil.rmtree(temp_dir)
            self.log.info(f"Process complete. Final video at: {final_video_path}")
            return final_video_path

        except Exception as e:
            self.log.error(f"An unexpected error occurred in download_episode: {e}")
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return None

    class _VIU_API:
        def __init__(self, token, cookies_path, logger):
            self.token = token
            self.log = logger
            self.session = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
            self.headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-US,en;q=0.9',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            }
            if os.path.exists(cookies_path):
                self._load_cookies(cookies_path)

        def _load_cookies(self, file_path):
            try:
                cookie_jar = MozillaCookieJar(file_path)
                cookie_jar.load(ignore_discard=True, ignore_expires=True)
                self.session.cookies = cookie_jar
                self.log.info(f"Successfully loaded cookies from {file_path}")
            except Exception as e:
                self.log.error(f"Error loading cookies: {e}")

        async def get_product_series_id(self, url):
            try:
                response = await self.session.get(url, headers=self.headers)
                response.raise_for_status()
                
                content = response.text
                product_id_match = re.search(r'"product_id":\s*"(\d+)"', content)
                series_id_match = re.search(r'"series_id":\s*"(\d+)"', content)
                series_name_match = re.search(r'"series_name":\s*"(.*?)"', content)
                
                if not product_id_match or not series_id_match or not series_name_match:
                    self.log.warning("Could not find all required IDs/name in the page content.")
                    return None
                
                product_id = product_id_match.group(1)
                series_id = series_id_match.group(1)
                series_name = series_name_match.group(1)

                episode_match = re.search(r'<h2[^>]*id="type_ep"[^>]*>Episod\s+(\d+)</h2>', content)
                formatted_name = f"{series_name} Episode {episode_match.group(1)}" if episode_match else series_name

                return product_id, series_id, formatted_name
            except Exception as e:
                self.log.error(f"Error in get_product_series_id: {e}")
                return None

        async def get_subtitle(self, product_id):
            api_url = "https://api-gateway-global.viu.com/api/mobile"
            params = {
                "platform_flag_label": "web", "area_id": "1001", "language_flag_id": "7",
                "countryCode": "MY", "ut": "0", "r": "/vod/detail", "product_id": product_id, "os_flag_id": "1"
            }
            headers = self.headers.copy()
            headers["authorization"] = f"Bearer {self.token}"
            
            try:
                response = await self.session.get(api_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                subtitles = []
                if "data" in data and "product_subtitle" in data["data"]:
                    for sub in data["data"]["product_subtitle"]:
                        subtitles.append({"name": sub.get("name", "N/A"), "url": sub.get("subtitle_url", "N/A")})
                return subtitles
            except Exception as e:
                self.log.error(f"Error in get_subtitle: {e}")
                return []
        
        async def get_ccs_product_id_for_single(self, product_id):
            params = {
                'platform_flag_label': 'web', 'area_id': '1001', 'language_flag_id': '3',
                'countryCode': 'MY', 'ut': '2', 'r': '/vod/detail', 'product_id': product_id, 'os_flag_id': '1',
            }
            headers = self.headers.copy()
            headers["authorization"] = f"Bearer {self.token}"
            
            try:
                response = await self.session.get('https://api-gateway-global.viu.com/api/mobile', params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data.get("data", {}).get("current_product", {}).get("ccs_product_id")
            except Exception as e:
                self.log.error(f"Error getting CCS Product ID: {e}")
                return None

        async def get_manifest(self, ccs_product_id):
            url = "https://api-gateway-global.viu.com/api/playback/distribute"
            params = {
                "platform_flag_label": "web", "area_id": "1001", "language_flag_id": "7",
                "countryCode": "MY", "ut": "1", "ccs_product_id": ccs_product_id
            }
            headers = self.headers.copy()
            headers["authorization"] = f"Bearer {self.token}"
            
            try:
                response = await self.session.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                stream_urls = data.get("data", {}).get("stream", {}).get("url", {})
                manifests = {
                    "240P": stream_urls.get("s240p"), "480P": stream_urls.get("s480p"),
                    "720P": stream_urls.get("s720p"), "1080P": stream_urls.get("s1080p"),
                }
                return {k: v for k, v in manifests.items() if v}
            except Exception as e:
                self.log.error(f"Error in get_manifest: {e}")
                return None

        async def download_file_http(self, url, output_path):
            async with self.session.stream("GET", url) as response:
                response.raise_for_status()
                with open(output_path, 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
