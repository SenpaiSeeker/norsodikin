import asyncio
import os
import re
import time
import uuid
from functools import partial
from types import SimpleNamespace
from typing import Optional, List
from urllib.parse import urlparse, parse_qs

import aiohttp
import aiofiles
from .viu_ckey import ViuCKey


class ViuDownloader:
    def __init__(self, download_path: str = "downloads", region: str = "th"):
        self.download_path = download_path
        self.region = region
        self.base_url = "https://www.viu.com"
        self.api_gateway = "https://api-gateway-global.viu.com"
        
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
    
    def _extract_product_id(self, url: str) -> Optional[str]:
        pattern = r'/vod/(\d+)/'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None
    
    async def _get_video_info(self, product_id: str) -> dict:
        api_url = f"{self.base_url}/ott/{self.region}/index.php"
        params = {
            'r': 'vod/ajax-detail',
            'platform_flag_label': 'web',
            'user_id': 'undefined',
            'product_id': product_id
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': f'{self.base_url}/ott/{self.region}/',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    raise Exception(f"Failed to get video info: HTTP {response.status}")
    
    def _generate_ckey(self, vid: str, tm: str, platform: str = "web") -> str:
        ckey_generator = ViuCKey()
        
        app_ver = "1.0"
        guid = str(uuid.uuid4())
        url = f"{self.api_gateway}/api/playback/distribute"
        
        ckey = ckey_generator.make(
            vid=vid,
            tm=tm,
            app_ver=app_ver,
            guid=guid,
            platform=platform,
            url=url
        )
        
        return ckey
    
    async def _get_m3u8_url(self, ccs_product_id: str) -> str:
        tm = str(int(time.time()))
        ckey = self._generate_ckey(ccs_product_id, tm)
        
        api_url = f"{self.api_gateway}/api/playback/distribute"
        
        params = {
            'ccs_product_id': ccs_product_id,
            'r': 'vod/ajax-detail',
            'platform_flag_label': 'web',
            'area_id': '1',
            'language_flag_id': '1',
            'cKey': ckey,
            'timestamp': tm
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': f'{self.base_url}/ott/{self.region}/',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data and 'stream' in data['data']:
                        stream_data = data['data']['stream']
                        if 'url' in stream_data:
                            return stream_data['url']
                        elif 'playlist' in stream_data:
                            return stream_data['playlist'][0]['url']
                    raise Exception("M3U8 URL not found in API response")
                else:
                    raise Exception(f"Failed to get M3U8 URL: HTTP {response.status}")
    
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
                    # Parse progress from ffmpeg output
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
        
        if 'data' not in video_info:
            raise Exception("Failed to get video information")
        
        data = video_info['data']
        
        ccs_product_id = data.get('ccs_product_id') or data.get('product', {}).get('ccs_product_id')
        title = data.get('synopsis', {}).get('name') or data.get('product', {}).get('series', {}).get('name', 'video')
        episode_number = data.get('synopsis', {}).get('episode_number') or data.get('product', {}).get('number', '')
        
        if not ccs_product_id:
            raise Exception("Could not find ccs_product_id in video info")
        
        safe_title = re.sub(r'[\\/*?:"<>|]', '', title)
        if episode_number:
            safe_title = f"{safe_title}_EP{episode_number}"
        
        m3u8_url = await self._get_m3u8_url(ccs_product_id)
        
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
        if include_subtitles and 'subtitle' in data:
            subtitle_list = data['subtitle']
            
            for subtitle in subtitle_list:
                lang_code = subtitle.get('code', '').lower()
                lang_name = subtitle.get('name', lang_code)
                sub_url = subtitle.get('url')
                
                if not sub_url:
                    continue
                
                if subtitle_languages and lang_code not in subtitle_languages:
                    continue
                
                sub_filename = f"{safe_title}_{lang_name}.srt"
                sub_path = os.path.join(self.download_path, sub_filename)
                
                success = await self._download_subtitle(sub_url, sub_path)
                if success:
                    subtitle_paths.append({
                        'language': lang_name,
                        'code': lang_code,
                        'path': sub_path
                    })
        
        return SimpleNamespace(
            video_path=video_path,
            title=title,
            episode_number=episode_number,
            subtitle_paths=subtitle_paths,
            product_id=product_id,
            ccs_product_id=ccs_product_id
        )
    
    async def get_available_subtitles(self, url: str) -> List[dict]:
        product_id = self._extract_product_id(url)
        if not product_id:
            raise ValueError("Invalid Viu URL")
        
        video_info = await self._get_video_info(product_id)
        
        if 'data' not in video_info or 'subtitle' not in video_info['data']:
            return []
        
        subtitles = []
        for subtitle in video_info['data']['subtitle']:
            subtitles.append({
                'code': subtitle.get('code', '').lower(),
                'name': subtitle.get('name', ''),
                'url': subtitle.get('url', '')
            })
        
        return subtitles
