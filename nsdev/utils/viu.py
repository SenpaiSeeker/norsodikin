import os
import re
import subprocess
import requests
from http.cookiejar import MozillaCookieJar
from types import SimpleNamespace

from ..utils.logger import LoggerHandler

class ViuDownloader:
    def __init__(self, auth_token: str, cookies_path: str = "cookies.txt"):
        if not auth_token:
            raise ValueError("VIU authorization token is required.")
        if not os.path.exists(cookies_path):
            raise FileNotFoundError(f"Cookies file not found at: {cookies_path}")

        self.token = auth_token
        self.session = requests.Session()
        self.log = LoggerHandler()
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }
        self._load_cookies(cookies_path)

    def _load_cookies(self, file_path):
        try:
            cookie_jar = MozillaCookieJar(file_path)
            cookie_jar.load(ignore_discard=True, ignore_expires=True)
            self.session.cookies = cookie_jar
            self.log.print(f"{self.log.GREEN}Successfully loaded VIU cookies from {file_path}{self.log.RESET}")
        except Exception as e:
            self.log.print(f"{self.log.RED}Error loading cookies: {e}{self.log.RESET}")
            raise IOError(f"Failed to load cookies: {e}")

    def _extract_product_id(self, url: str) -> str:
        pattern = r'viu\.com/.*?/vod/(\d+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        raise ValueError("Could not extract a valid Product ID from the URL.")

    def get_episode_details(self, url: str) -> SimpleNamespace:
        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            html_content = response.text

            series_pattern = r'"series_id":\s*"(\d+)",\s*"series_name":\s*"(.*?)",\s*"product_id":\s*"(\d+)"'
            series_match = re.search(series_pattern, html_content)

            if not series_match:
                raise ValueError("Could not find series information on the page.")

            series_id = series_match.group(1)
            series_name = series_match.group(2)
            product_id = series_match.group(3)
            
            episode_pattern = r'<h2[^>]*id="type_ep"[^>]*>Episod\s+(\d+)</h2>'
            episode_match = re.search(episode_pattern, html_content)
            
            episode_number = episode_match.group(1) if episode_match else "1"
            formatted_name = f"{series_name} - Episode {episode_number}"

            subtitles = self._5get_subtitles(product_id)
            resolutions = self._get_manifests(series_id)

            return SimpleNamespace(
                name=formatted_name,
                product_id=product_id,
                series_id=series_id,
                ccs_product_id=series_id,
                subtitles=subtitles,
                resolutions=resolutions
            )
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to fetch VIU page: {e}")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred while getting episode details: {e}")

    def _get_subtitles(self, product_id: str) -> list:
        api_url = "https://api-gateway-global.viu.com/api/mobile"
        params = {
            "platform_flag_label": "web", "area_id": "1001", "language_flag_id": "7",
            "countryCode": "MY", "ut": "0", "r": "/vod/detail", "product_id": product_id, "os_flag_id": "1"
        }
        headers = self.headers.copy()
        headers["authorization"] = f"Bearer {self.token}"
        
        response = self.session.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        subtitle_list = []
        if "data" in data and "product_subtitle" in data["data"]:
            for sub in data["data"]["product_subtitle"]:
                subtitle_list.append(SimpleNamespace(name=sub.get("name"), url=sub.get("subtitle_url")))
        return subtitle_list

    def _get_manifests(self, ccs_product_id: str) -> dict:
        api_url = "https://api-gateway-global.viu.com/api/playback/distribute"
        params = {
            "platform_flag_label": "web", "area_id": "1001", "language_flag_id": "7",
            "countryCode": "MY", "ut": "1", "ccs_product_id": ccs_product_id
        }
        headers = self.headers.copy()
        headers["authorization"] = f"Bearer {self.token}"
        
        response = self.session.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        stream_urls = data.get("data", {}).get("stream", {}).get("url", {})
        manifests = {
            "240p": stream_urls.get("s240p"),
            "480p": stream_urls.get("s480p"),
            "720p": stream_urls.get("s720p"),
            "1080p": stream_urls.get("s1080p"),
        }
        return {k: v for k, v in manifests.items() if v}

    def download_and_merge(self, m3u8_url: str, subtitle_url: str, save_dir: str, file_name: str) -> str:
        os.makedirs(save_dir, exist_ok=True)
        
        base_filename = re.sub(r'[\\/*?:"<>|]', "", file_name)
        raw_video_path = os.path.join(save_dir, f"{base_filename}_raw.mp4")
        subtitle_path = os.path.join(save_dir, f"{base_filename}.srt")
        final_video_path = os.path.join(save_dir, f"{base_filename}.mp4")

        try:
            self.log.print(f"{self.log.CYAN}Downloading HLS stream...{self.log.RESET}")
            hls_command = [
                "N_m3u8DL-RE", m3u8_url,
                "--save-name", f"{base_filename}_raw",
                "--save-dir", save_dir,
                "--thread-count", "8",
                "-mt", "-M", "format=mp4"
            ]
            subprocess.run(hls_command, check=True, capture_output=True, text=True)
            if not os.path.exists(raw_video_path):
                raise FileNotFoundError("HLS download did not produce the expected video file.")

            self.log.print(f"{self.log.CYAN}Downloading subtitle...{self.log.RESET}")
            sub_response = requests.get(subtitle_url)
            sub_response.raise_for_status()
            with open(subtitle_path, 'wb') as f:
                f.write(sub_response.content)

            self.log.print(f"{self.log.CYAN}Merging video and subtitles with FFmpeg...{self.log.RESET}")
            merge_command = [
                "ffmpeg", "-y",
                "-i", raw_video_path,
                "-i", subtitle_path,
                "-c", "copy",
                "-c:s", "mov_text",
                "-metadata:s:s:0", "language=ind",
                final_video_path
            ]
            result = subprocess.run(merge_command, check=True, capture_output=True, text=True)
            self.log.print(f"{self.log.GREEN}Successfully merged video to: {final_video_path}{self.log.RESET}")
            return final_video_path

        except subprocess.CalledProcessError as e:
            self.log.error(f"A command-line tool failed:\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}")
            raise RuntimeError(f"Process failed: {e.stderr}")
        except Exception as e:
            self.log.error(f"An error occurred during download/merge: {e}")
            raise
        finally:
            if os.path.exists(raw_video_path):
                os.remove(raw_video_path)
            if os.path.exists(subtitle_path):
                os.remove(subtitle_path)
