import asyncio
import os
from functools import partial

import requests
from yt_dlp import YoutubeDL


class MediaDownloader:
    def __init__(self, download_path: str = "downloads", cookies_file_path: str = None):
        self.download_path = download_path
        self.cookies_file_path = cookies_file_path
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def _sync_download(
        self, url: str, audio_only: bool, progress_callback: callable, on_start_entry_callback: callable, loop: asyncio.AbstractEventLoop
    ) -> list:
        
        def _hook(d):
            if d['status'] == 'downloading' and progress_callback:
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                if total_bytes:
                    asyncio.run_coroutine_threadsafe(
                        progress_callback(d['downloaded_bytes'], total_bytes), 
                        loop
                    )

        ydl_opts = {
            "outtmpl": os.path.join(self.download_path, "%(playlist_index)s - %(title)s.%(ext)s" if 'playlist' in url else "%(title)s.%(ext)s"),
            "quiet": True,
            "noplaylist": False, 
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

        
        results = []
        with YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(url, download=False)
            
            entries = playlist_info.get('entries', [playlist_info])
            total_entries = len(entries)

            for i, entry in enumerate(entries):
                if on_start_entry_callback:
                    asyncio.run_coroutine_threadsafe(
                        on_start_entry_callback(i + 1, total_entries, entry),
                        loop
                    ).result()

                info = ydl.extract_info(entry['url'], download=True)
                filename = ydl.prepare_filename(info)
                if audio_only:
                    base, _ = os.path.splitext(filename)
                    filename = base + ".mp3"

                thumbnail_data = None
                thumbnail_url = info.get("thumbnail")
                if thumbnail_url:
                    try:
                        thumb_response = requests.get(thumbnail_url)
                        thumb_response.raise_for_status()
                        thumbnail_data = thumb_response.content
                    except requests.RequestException:
                        thumbnail_data = None

                results.append({
                    "path": filename,
                    "title": info.get("fulltitle", "N/A"),
                    "duration": info.get("duration", 0),
                    "thumbnail_data": thumbnail_data,
                })
        
        return results

    async def download(
        self, url: str, audio_only: bool = False, progress_callback: callable = None, on_start_entry_callback: callable = None
    ) -> list:
        loop = asyncio.get_running_loop()
        try:
            func_call = partial(self._sync_download, url, audio_only, progress_callback, on_start_entry_callback, loop)
            results = await loop.run_in_executor(None, func_call)
            return results
        except Exception as e:
            raise Exception(f"Failed to download media: {e}")
