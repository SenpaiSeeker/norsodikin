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
        results = s.results.dict()

        image_bytes = BytesIO(s.results.share(image_format="png"))
        image_bytes.name = "speedtest.png"
        return image_bytes

    async def run(self) -> BytesIO:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_run_test)
