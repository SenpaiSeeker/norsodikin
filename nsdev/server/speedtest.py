import asyncio
import functools
from io import BytesIO

import httpx
import speedtest


class SpeedtestRunner:
    def _sync_run_test(self) -> BytesIO:
        s = speedtest.Speedtest()
        s.get_best_server()
        s.download()
        s.upload()
        
        image_url = s.results.share()
        with httpx.Client(follow_redirects=True) as client:
            response = client.get(image_url)
            response.raise_for_status()
            image_bytes = BytesIO(response.content)
            image_bytes.name = "speedtest.png"
            return image_bytes

    async def run(self) -> BytesIO:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_run_test)
