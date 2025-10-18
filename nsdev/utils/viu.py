import asyncio
import os
import re
import time
import uuid
import json
from functools import partial
from types import SimpleNamespace
from typing import Optional, List
from urllib.parse import urlparse, parse_qs

import aiohttp
import aiofiles


class ViuDownloader:
    def __init__(self, download_path: str = "downloads", region: str = "id"):
        self.download_path = download_path
        self.region = region.lower()
        self.base_url = "https://www.viu.com"
        self.api_base = "https://um.viuapi.io"
        
        self.device_id = str(uuid.uuid4())
        self.session_id = str(uuid.uuid4())
        self.token = None
        
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
    
    def _extract_product_id(self, url: str) -> Optional[str]:
        patterns = [
            r'/vod/(\d+)',
            r'/video-[\w-]+-(\d+)',
            r'/all/video-[\w-]+-(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def _get_token(self) -> str:
        api_url = f"{self.api_base}/user/identity"
        
        headers = {
            'Content-Type': 'application/json',
            'x-session-id': self.session_id,
            'x-client': 'browser',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        params = {
            'ver': 1.0,
            'fmt': 'json',
            'aver': 5.0,
            'appver': 2.0,
            'appid': 'viu_desktop',
            'platform': 'desktop',
            'iid': self.device_id
        }
        
        data = json.dumps({'deviceId': self.device_id})
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, params=params, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('token')
                else:
                    raise Exception(f"Failed to get authentication token: HTTP {response.status}")
    
    async def _get_video_info(self, product_id: str) -> dict:
        if not self.token:
            self.token = await self._get_token()
        
        api_url = f"{self.api_base}/drm/v1/content/{product_id}"
        
        headers = {
            'Authorization': self.token,
            'x-session-id': self.session_id,
            'x-client': 'browser',
            'ccode': self.region.upper(),
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': self.base_url,
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, data=b'') as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    raise Exception(f"Failed to get video info: HTTP {response.status}")
    
    async def _get_webpage_metadata(self, url: str) -> dict:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()

                    metadata = {}

                    initial_state_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', html, re.DOTALL)
                    if initial_state_match:
                        try:
                            initial_state = json.loads(initial_state_match.group(1))
                            clip_details = initial_state.get('content', {}).get('clipDetails', {})
                            
                            metadata['title'] = clip_details.get('title') or clip_details.get('display_title')
                            metadata['description'] = clip_details.get('description')
                            metadata['duration'] = clip_details.get('duration')
                            metadata['episode_number'] = clip_details.get('episode_no') or clip_details.get('episodeno')
                            
                            subtitles = []
                            for key, value in clip_details.items():
                                match = re.match(r'^subtitle_([\\w-]+)_(\\w+)$', key)
                                if match and value:
                                    lang, ext = match.groups()
                                    subtitles.append({
                                        'language': lang,
                                        'ext': ext,
                                        'url': value
                                    })
                            metadata['subtitles'] = subtitles
                        except:
                            pass
                    
                    return metadata
                return {}
    
    async def _download_subtitle(self, subtitle_url: str, output_path: str):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(subtitle_url, headers=headers) as response:
                if response.status == 200:
                    content = await response.read()
                    async with aiofiles.open(output_path, 'wb') as f:
                        await f.write(content)
                    return True
                return False
    
    def _sync_download_video(
        self,
        m3u8_url: str,
        output_path: str,
        progress_callback: callable,
        loop: asyncio.AbstractEventLoop
    ) -> str:
        import subprocess
        
        cmd = [
            'ffmpeg',
            '-i', m3u8_url,
            '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            '-y',
            output_path
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            for line in process.stderr:
                if progress_callback and 'time=' in line:
                    asyncio.run_coroutine_threadsafe(
                        progress_callback(line),
                        loop
                    )
            
            process.wait()
            
            if process.returncode == 0:
                return output_path
            else:
                raise Exception(f"FFmpeg failed with return code {process.returncode}")
                
        except FileNotFoundError:
            raise Exception("FFmpeg not found. Please install ffmpeg to download videos.")
        except Exception as e:
            raise Exception(f"Failed to download video: {e}")
    
    async def download(
        self,
        url: str,
        audio_only: bool = False,
        include_subtitles: bool = True,
        subtitle_languages: Optional[List[str]] = None,
        progress_callback: callable = None
    ) -> SimpleNamespace:
        product_id = self._extract_product_id(url)
        if not product_id:
            raise ValueError("Invalid Viu URL. Could not extract product ID.")
        
        video_info = await self._get_video_info(product_id)
        
        if not video_info.get('playUrl'):
            raise Exception("Failed to get video playback URL")
        
        m3u8_url = video_info['playUrl']
        
        metadata = await self._get_webpage_metadata(url)
        
        title = metadata.get('title') or f'VIU_Video_{product_id}'
        episode_number = metadata.get('episode_number') or ''
        
        safe_title = re.sub(r'[\\/*?:"<>|]', '', title)
        if episode_number:
            safe_title = f"{safe_title}_EP{episode_number}"
        
        video_filename = f"{safe_title}.mp4"
        video_path = os.path.join(self.download_path, video_filename)
        
        loop = asyncio.get_running_loop()
        video_path = await loop.run_in_executor(
            None,
            partial(
                self._sync_download_video,
                m3u8_url,
                video_path,
                progress_callback,
                loop
            )
        )
        
        subtitle_paths = []
        if include_subtitles and metadata.get('subtitles'):
            for subtitle in metadata['subtitles']:
                lang = subtitle.get('language', 'und')
                ext = subtitle.get('ext', 'srt')
                sub_url = subtitle.get('url')
                
                if not sub_url:
                    continue
                
                if subtitle_languages and lang not in subtitle_languages:
                    continue
                
                sub_filename = f"{safe_title}_{lang}.{ext}"
                sub_path = os.path.join(self.download_path, sub_filename)
                
                success = await self._download_subtitle(sub_url, sub_path)
                if success:
                    subtitle_paths.append({
                        'language': lang,
                        'code': lang,
                        'path': sub_path
                    })
        
        return SimpleNamespace(
            video_path=video_path,
            title=title,
            episode_number=episode_number,
            subtitle_paths=subtitle_paths,
            product_id=product_id,
            ccs_product_id=product_id
        )
    
    async def get_available_subtitles(self, url: str) -> List[dict]:
        metadata = await self._get_webpage_metadata(url)
        return metadata.get('subtitles', [])
