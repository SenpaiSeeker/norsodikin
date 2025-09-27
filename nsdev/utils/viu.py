import asyncio
import json
import os
import re
import subprocess
from http.cookiejar import MozillaCookieJar
from types import SimpleNamespace

import httpx
from bs4 import BeautifulSoup


class ViuDownloader:
    def __init__(self, token: str, cookies_file: str = "cookies.txt"):
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
        self.token = token
        self.cookies_file = cookies_file
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }
        self.session = httpx.AsyncClient(timeout=30, follow_redirects=True)
        self.session.headers.update(self.headers)
        self._load_cookies()

    def _load_cookies(self):
        if not os.path.isfile(self.cookies_file):
            raise FileNotFoundError(f"Cookies file not found: {self.cookies_file}")
        try:
            cookie_jar = MozillaCookieJar(self.cookies_file)
            cookie_jar.load(ignore_discard=True, ignore_expires=True)
            self.session.cookies = cookie_jar
        except Exception as e:
            raise IOError(f"Error loading cookies: {e}")

    async def get_episode_details(self, url: str) -> SimpleNamespace:
        try:
            response = await self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')
            initial_state_script = soup.find('script', string=re.compile('window.__INITIAL_STATE__'))
            
            if not initial_state_script:
                raise ValueError("Could not find __INITIAL_STATE__ script on the page. The page structure may have changed.")

            json_text = initial_state_script.string.split(' = ', 1)[1].rstrip(';')
            data = json.loads(json_text)
            
            vod_data = data.get('VOD', {})
            product_id = vod_data.get('current_product', {}).get('product_id')
            series_id = vod_data.get('current_product', {}).get('series_id')
            series_name = vod_data.get('current_product', {}).get('series_name', 'Unknown Series')
            episode_number = vod_data.get('current_product', {}).get('number', '')
            
            if not all([product_id, series_id]):
                raise ValueError("Could not extract 'product_id' or 'series_id' from the state data.")
                
            clean_series_name = re.sub(r'[\?:]', '', series_name)
            formatted_name = f"{clean_series_name} Episode {episode_number}" if episode_number else clean_series_name
            
            return SimpleNamespace(
                product_id=str(product_id),
                series_id=str(series_id),
                formatted_name=formatted_name
            )
        except Exception as e:
            raise Exception(f"Failed to get episode details: {e}")

    async def get_available_subtitles(self, product_id: str) -> list:
        api_url = "https://api-gateway-global.viu.com/api/mobile"
        params = {
            "platform_flag_label": "web", "area_id": "1001", "language_flag_id": "7",
            "countryCode": "ID", "ut": "0", "r": "/vod/detail", "product_id": product_id, "os_flag_id": "1"
        }
        headers = {'authorization': f"Bearer {self.token}"}
        
        try:
            response = await self.session.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            subtitles = []
            if "data" in data and "product_subtitle" in data["data"]:
                for sub in data["data"]["product_subtitle"]:
                    subtitles.append({'name': sub.get("name", "N/A"), 'url': sub.get("subtitle_url", "N/A")})
            return subtitles
        except Exception as e:
            raise Exception(f"Failed to fetch subtitles: {e}")

    async def get_available_resolutions(self, product_id: str) -> dict:
        api_url = "https://api-gateway-global.viu.com/api/playback/distribute"
        params = {"platform_flag_label": "web", "area_id": "1001", "language_flag_id": "7", 
                  "countryCode": "ID", "ut": "1", "ccs_product_id": product_id}
        headers = {'authorization': f"Bearer {self.token}"}
        
        try:
            response = await self.session.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json().get("data", {}).get("stream", {}).get("url", {})
            
            resolutions = {
                "240p": data.get("s240p"), "480p": data.get("s480p"),
                "720p": data.get("s720p"), "1080p": data.get("s1080p"),
            }
            return {k: v for k, v in resolutions.items() if v}
        except Exception as e:
            raise Exception(f"Failed to get resolutions: {e}")

    async def download_episode(self, video_url: str, subtitle_url: str, filename: str, progress_callback=None) -> str:
        clean_filename = re.sub(r'[\\/*?:"<>|]', "", filename)
        base_filename = os.path.join("downloads", clean_filename.replace(' ', '_'))
        video_path = f"{base_filename}.mp4"
        subtitle_path = f"{base_filename}.srt"
        final_path = f"{base_filename}-merged.mp4"
        
        try:
            if subtitle_url:
                async with self.session.stream("GET", subtitle_url) as r:
                    r.raise_for_status()
                    with open(subtitle_path, 'wb') as f:
                        async for chunk in r.aiter_bytes():
                            f.write(chunk)
            
            downloader_cmd = [
                './N_m3u8DL-RE', video_url,
                '--save-name', f'"{clean_filename}"',
                '--save-dir', 'downloads',
                '--thread-count', '16', '-mt',
                '-M', 'format=mp4'
            ]
            process = await asyncio.create_subprocess_shell(
                " ".join(downloader_cmd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await self._read_stream(process.stdout, progress_callback, "Downloading")
            await process.wait()

            if process.returncode != 0:
                stderr = await process.stderr.read()
                raise Exception(f"N_m3u8DL-RE failed: {stderr.decode()}")

            if subtitle_url:
                if progress_callback:
                    await progress_callback("Merging files...")

                merge_cmd = [
                    'ffmpeg', '-i', f'"{video_path}"', '-i', f'"{subtitle_path}"',
                    '-c', 'copy', '-c:s', 'mov_text',
                    '-metadata:s:s:0', 'language=ind',
                    '-disposition:s:0', 'default',
                    f'"{final_path}"', '-y'
                ]
                process = await asyncio.create_subprocess_shell(
                    " ".join(merge_cmd),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.wait()
                if process.returncode != 0:
                    stderr = await process.stderr.read()
                    raise Exception(f"FFmpeg merge failed: {stderr.decode()}")
                
                return final_path
            else:
                return video_path
        finally:
            if subtitle_url and os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(subtitle_path):
                os.remove(subtitle_path)

    async def _read_stream(self, stream, callback, task_name):
        if not callback:
            return
        
        while True:
            line = await stream.readline()
            if not line:
                break
            line_str = line.decode().strip()
            
            progress_match = re.search(r'(\d+\.\d+)%', line_str)
            if progress_match:
                progress = float(progress_match.group(1))
                await callback(f"{task_name} {progress:.2f}%")
