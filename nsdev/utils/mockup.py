import base64

from playwright.async_api import async_playwright


class DeviceMockup:
    async def wrap_in_frame(self, screenshot_bytes: bytes, device_type: str = "iphone_14_pro") -> bytes:
        screenshot_base64 = "data:image/png;base64," + base64.b64encode(screenshot_bytes).decode()

        html_content = self._generate_html(screenshot_base64, device_type)

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1200, "height": 1200}, device_scale_factor=2)

            await page.set_content(html_content)
            await page.wait_for_selector(".device-wrapper")

            element = await page.query_selector(".device-wrapper")
            screenshot_bytes = await element.screenshot(omit_background=True)

            await browser.close()
            return screenshot_bytes

    def _generate_html(self, image_src: str, device_type: str) -> str:
        device_css = ""

        if device_type == "iphone_14_pro":
            device_css = """
                .device {
                    width: 380px;
                    height: 780px;
                    background: #000;
                    border-radius: 50px;
                    position: relative;
                    box-shadow: 0 0 0 12px #333, 0 0 0 14px #555, 0 20px 50px rgba(0,0,0,0.5);
                    overflow: hidden;
                }
                .notch {
                    position: absolute;
                    top: 15px;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 100px;
                    height: 30px;
                    background: #000;
                    border-radius: 20px;
                    z-index: 10;
                }
                .screen {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    border-radius: 40px;
                }
            """
        elif device_type == "macbook":
            device_css = """
                .device {
                    width: 800px;
                    height: 500px;
                    background: #1a1a1a;
                    border-radius: 20px 20px 0 0;
                    position: relative;
                    box-shadow: 0 20px 50px rgba(0,0,0,0.5);
                    padding: 20px 20px 0 20px;
                    box-sizing: border-box;
                }
                .screen {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    border-radius: 8px 8px 0 0;
                }
                .base {
                    position: absolute;
                    bottom: -20px;
                    left: 0;
                    width: 100%;
                    height: 20px;
                    background: #2a2a2a;
                    border-radius: 0 0 20px 20px;
                }
                .notch { display: none; }
            """
        else:
            device_css = """
                .device {
                    width: 360px;
                    height: 760px;
                    background: #000;
                    border-radius: 30px;
                    position: relative;
                    box-shadow: 0 0 0 8px #222, 0 20px 50px rgba(0,0,0,0.5);
                    overflow: hidden;
                }
                .notch {
                    position: absolute;
                    top: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 20px;
                    height: 20px;
                    background: #000;
                    border-radius: 50%;
                    z-index: 10;
                }
                .screen {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    border-radius: 25px;
                }
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    margin: 0;
                    padding: 50px;
                    background: transparent;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
                .device-wrapper {{
                    padding: 20px;
                }}
                {device_css}
            </style>
        </head>
        <body>
            <div class="device-wrapper">
                <div class="device">
                    <div class="notch"></div>
                    <img src="{image_src}" class="screen" />
                    <div class="base"></div>
                </div>
            </div>
        </body>
        </html>
        """
