import asyncio
import os
from yt_dlp import YoutubeDL

class MediaDownloader:
    def __init__(self, download_path: str = "downloads", cookies_file_path: str = None):
        self.download_path = download_path
        self.cookies_file_path = cookies_file_path 
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def _sync_download(self, url: str, audio_only: bool) -> dict:
        ydl_opts = {
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'quiet': True,
        }

        if self.cookies_file_path and os.path.exists(self.cookies_file_path):
            ydl_opts['cookiefile'] = self.cookies_file_path

        if audio_only:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if audio_only:
                base, _ = os.path.splitext(filename)
                filename = base + '.mp3'

            return {
                'path': filename,
                'title': info.get('title', 'N/A'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', None)
            }

    async def download(self, url: str, audio_only: bool = False) -> dict:
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                None, self._sync_download, url, audio_only
            )
            return result
        except Exception as e:
            raise Exception(f"Failed to download media: {e}")
