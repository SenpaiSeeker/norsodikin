import asyncio
import os
from functools import partial
from types import SimpleNamespace
from urllib.parse import quote
import shutil

try:
    from pinterest_dl import PinterestDL
    PINTEREST_DL_AVAILABLE = True
except ImportError:
    PINTEREST_DL_AVAILABLE = False

import httpx


class PinterestDownloader:
    def __init__(self, download_path: str = "downloads/pinterest"):
        if not PINTEREST_DL_AVAILABLE:
            raise ImportError(
                "pinterest-dl library diperlukan. Install dengan:\n"
                "pip install git+https://github.com/sean1832/pinterest-dl.git"
            )

        self.download_path = download_path
        self.downloader = PinterestDL.with_api(
            timeout=10,
            verbose=False,
            ensure_alt=True
        )

        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def _sync_download(self, url: str):
        temp_dir = os.path.join(self.download_path, "_temp")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            images = self.downloader.scrape_and_download(
                url=url,
                output_dir=temp_dir,
                num=1,
                download_streams=True,
                min_resolution=(512, 512),
                caption="none",
                delay=0.5
            )

            if not images:
                raise Exception("Download gagal")

            file_path = images[0].get("file_path", "")
            if not os.path.exists(file_path):
                raise Exception("File tidak ditemukan")

            ext = os.path.splitext(file_path)[1].lower()
            new_path = os.path.join(self.download_path, f"pinterest_media{ext}")

            shutil.move(file_path, new_path)
            shutil.rmtree(temp_dir, ignore_errors=True)

            return SimpleNamespace(
                path=new_path,
                url=url,
                type="video" if ext in [".mp4", ".mov", ".webm"] else "image"
            )

        except:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    async def download_from_url(self, url: str):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._sync_download, url))

    def _sync_search(self, query: str, limit: int):
        temp_dir = os.path.join(self.download_path, "_temp")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            search_url = f"https://www.pinterest.com/search/pins/?q={quote(query)}"

            images = self.downloader.scrape_and_download(
                url=search_url,
                output_dir=temp_dir,
                num=limit,
                download_streams=True,
                min_resolution=(512, 512),
                caption="none",
                delay=0.5
            )

            results = []

            for img in images:
                file_path = img.get("file_path", "")
                if os.path.exists(file_path):
                    ext = os.path.splitext(file_path)[1].lower()
                    new_path = os.path.join(self.download_path, f"pinterest_media{ext}")

                    shutil.move(file_path, new_path)

                    results.append(
                        SimpleNamespace(
                            path=new_path,
                            url=search_url,
                            type="video" if ext in [".mp4", ".mov", ".webm"] else "image"
                        )
                    )

            shutil.rmtree(temp_dir, ignore_errors=True)
            return results

        except:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    async def download_from_query(self, query: str, limit: int = 5):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._sync_search, query, limit))

    async def get_media_info(self, url: str):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, follow_redirects=True)

                if response.status_code == 200:
                    return SimpleNamespace(
                        url=url,
                        title="Pinterest Media",
                        type="unknown",
                        available=True
                    )

                return None

        except:
            return None
