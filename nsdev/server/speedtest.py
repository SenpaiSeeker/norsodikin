import asyncio
import functools
from io import BytesIO

import speedtest
from PIL import Image, ImageDraw, ImageFont

from ..utils.font_manager import FontManager


class SpeedtestRunner(FontManager):
    def _sync_run_test(self) -> BytesIO:
        s = speedtest.Speedtest()
        s.get_best_server()
        s.download()
        s.upload()
        res = s.results.dict()

        ping = res["ping"]
        download = res["download"] / 1024 / 1024
        upload = res["upload"] / 1024 / 1024
        
        font_main = self._get_font_from_package("NotoSans-Bold.ttf", 30)
        font_sub = self._get_font_from_package("NotoSans-Regular.ttf", 24)
        
        img = Image.new('RGB', (800, 450), color = '#1e1e1e')
        draw = ImageDraw.Draw(img)

        draw.text((40, 40), "Server Speed Test Result", font=font_main, fill="#FFFFFF")
        
        draw.text((60, 120), "Ping", font=font_sub, fill="#AAAAAA")
        draw.text((60, 150), f"{ping:.2f} ms", font=font_main, fill="#4CAF50")
        
        draw.text((300, 120), "Download", font=font_sub, fill="#AAAAAA")
        draw.text((300, 150), f"{download:.2f} Mbps", font=font_main, fill="#2196F3")
        
        draw.text((540, 120), "Upload", font=font_sub, fill="#AAAAAA")
        draw.text((540, 150), f"{upload:.2f} Mbps", font=font_main, fill="#9C27B0")
        
        client_info = f"ISP: {res['client']['isp']} ({res['client']['ip']})"
        server_info = f"Server: {res['server']['name']} ({res['server']['country']})"
        draw.text((40, 350), client_info, font=font_sub, fill="#FFFFFF")
        draw.text((40, 380), server_info, font=font_sub, fill="#FFFFFF")
        
        output_buffer = BytesIO()
        img.save(output_buffer, "PNG")
        output_buffer.name = "speedtest.png"
        return output_buffer

    async def run(self) -> BytesIO:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_run_test)
