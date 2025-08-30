import asyncio
import json
import os
from functools import partial

from yt_dlp import YoutubeDL


class MediaDownloader:
    def __init__(self, download_path: str = "downloads", cookies_file_path: str = None):
        self.download_path = download_path
        self.cookies_file_path = cookies_file_path
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def _sync_download(self, url: str, audio_only: bool, progress_callback: callable, loop: asyncio.AbstractEventLoop) -> str:
        
        def _hook(d):
            if d['status'] == 'downloading' and progress_callback:
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                if total_bytes:
                    asyncio.run_coroutine_threadsafe(
                        progress_callback(d['downloaded_bytes'], total_bytes), 
                        loop
                    )

        ydl_opts = {
            "outtmpl": os.path.join(self.download_path, "%(title)s.%(ext)s"),
            "quiet": True,
            "ignoreerrors": True, 
        }
        
        if progress_callback:
            ydl_opts['progress_hooks'] = [_hook]

        if self.cookies_file_path and os.path.exists(self.cookies_file_path):
            ydl_opts["cookiefile"] = self.cookies_file_path
        
        if audio_only:
            ydl_opts.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                }
            )
        else:
            ydl_opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return json.dumps(info, indent=4)

    async def download(self, url: str, audio_only: bool = False, progress_callback: callable = None) -> str:
        loop = asyncio.get_running_loop()
        try:
            func_call = partial(self._sync_download, url, audio_only, progress_callback, loop)
            result_json = await loop.run_in_executor(None, func_call)
            return result_json
        except Exception as e:
            raise Exception(f"Failed to download media: {e}")
