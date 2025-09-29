import asyncio
import functools
from io import BytesIO

import speedtest


class SpeedtestRunner:
    def _sync_run_test(self) -> BytesIO:
        s = speedtest.Speedtest()
        s.get_best_server()
        s.download()
        s.upload()
        
        image_url = s.results.share()
        
        response = s.opener.open(image_url)
        image_data = response.read()
        
        image_bytes = BytesIO(image_data)
        image_bytes.name = "speedtest.png"
        return image_bytes

    async def run(self) -> BytesIO:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_run_test)
