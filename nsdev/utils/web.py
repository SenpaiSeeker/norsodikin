import asyncio

from playwright.async_api import async_playwright


class WebAutomation:
    async def screenshot(
        self, url: str, full_page: bool = False, mobile: bool = False, dark_mode: bool = False, wait_time: int = 2
    ) -> bytes:
        if not url.startswith("http"):
            url = "https://" + url

        viewport = {"width": 390, "height": 844} if mobile else {"width": 1920, "height": 1080}
        user_agent = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            if mobile
            else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            context_options = {
                "viewport": viewport,
                "user_agent": user_agent,
                "device_scale_factor": 2.0,
                "is_mobile": mobile,
                "has_touch": mobile,
            }

            if dark_mode:
                context_options["color_scheme"] = "dark"

            context = await browser.new_context(**context_options)
            page = await context.new_page()

            try:
                await page.goto(url, timeout=60000, wait_until="networkidle")

                if wait_time > 0:
                    await asyncio.sleep(wait_time)

                if dark_mode:
                    await page.evaluate("""() => {
                        document.documentElement.classList.add('dark');
                        document.body.classList.add('dark-mode');
                        document.body.style.backgroundColor = '#121212';
                        document.body.style.color = '#ffffff';
                    }""")

                await page.add_style_tag(
                    content="body { overflow-y: hidden !important; } ::-webkit-scrollbar { display: none; }"
                )

                screenshot_bytes = await page.screenshot(type="png", full_page=full_page)
                return screenshot_bytes

            except Exception as e:
                raise Exception(f"Gagal memuat halaman: {e}")
            finally:
                await browser.close()
