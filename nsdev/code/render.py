import asyncio
from playwright.async_api import async_playwright
from urllib.parse import quote

class CodeRenderer:
    async def render(self, code: str, language: str = "auto", theme: str = "dracula", line_numbers: bool = True) -> bytes:
        html_content = self._generate_html(code, language, theme, line_numbers)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
            
            await page.set_content(html_content)
            await page.wait_for_selector(".code-container")
            
            element = await page.query_selector(".code-container")
            screenshot_bytes = await element.screenshot(omit_background=True)
            
            await browser.close()
            return screenshot_bytes

    def _generate_html(self, code: str, language: str, theme: str, line_numbers: bool) -> str:
        line_numbers_class = "line-numbers" if line_numbers else ""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/{theme}.min.css">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 50px;
                    background: transparent;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-family: 'Fira Code', monospace;
                }}
                .code-container {{
                    background: #282a36;
                    border-radius: 12px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.55);
                    overflow: hidden;
                    min-width: 400px;
                    max-width: 1200px;
                }}
                .window-header {{
                    background: #21222c;
                    padding: 12px 16px;
                    display: flex;
                    gap: 8px;
                    align-items: center;
                }}
                .dot {{
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                }}
                .red {{ background: #ff5f56; }}
                .yellow {{ background: #ffbd2e; }}
                .green {{ background: #27c93f; }}
                
                pre {{
                    margin: 0;
                    padding: 20px;
                    overflow-x: auto;
                }}
                code {{
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 16px;
                    line-height: 1.5;
                }}
            </style>
        </head>
        <body>
            <div class="code-container">
                <div class="window-header">
                    <div class="dot red"></div>
                    <div class="dot yellow"></div>
                    <div class="dot green"></div>
                </div>
                <pre><code class="language-{language} {line_numbers_class}">{code}</code></pre>
            </div>
            <script>hljs.highlightAll();</script>
        </body>
        </html>
        """
