from datetime import datetime, timezone

from playwright.async_api import async_playwright


class WebArchiver:
    async def capture_evidence(self, url: str, output_path: str = "evidence.pdf") -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)

                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

                footer_html = f"""
                <div style="
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    width: 100%;
                    background-color: rgba(0, 0, 0, 0.8);
                    color: white;
                    padding: 10px;
                    font-family: monospace;
                    font-size: 12px;
                    z-index: 99999;
                    text-align: center;
                    border-top: 2px solid red;
                ">
                    <strong>DIGITAL EVIDENCE SNAPSHOT</strong><br>
                    URL: {url}<br>
                    Time: {timestamp}<br>
                    Archived by: Norsodikin WebArchiver
                </div>
                """

                await page.evaluate(f"document.body.insertAdjacentHTML('beforeend', `{footer_html}`)")

                await page.pdf(
                    path=output_path,
                    format="A4",
                    print_background=True,
                    margin={"top": "20px", "bottom": "60px", "left": "20px", "right": "20px"},
                )

                return output_path

            except Exception as e:
                raise RuntimeError(f"Failed to capture evidence: {e}")
            finally:
                await browser.close()

    async def capture_screenshot_evidence(self, url: str, output_path: str = "evidence.png") -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1280, "height": 720})

            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)

                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

                await page.evaluate(f"""
                    const div = document.createElement('div');
                    div.style.position = 'fixed';
                    div.style.top = '0';
                    div.style.left = '0';
                    div.style.width = '100%';
                    div.style.backgroundColor = 'red';
                    div.style.color = 'white';
                    div.style.fontWeight = 'bold';
                    div.style.textAlign = 'center';
                    div.style.zIndex = '100000';
                    div.style.padding = '5px';
                    div.style.fontSize = '14px';
                    div.innerText = 'SNAPSHOT: {timestamp} | {url}';
                    document.body.prepend(div);
                """)

                await page.screenshot(path=output_path, full_page=True)
                return output_path

            except Exception as e:
                raise RuntimeError(f"Failed to screenshot evidence: {e}")
            finally:
                await browser.close()
