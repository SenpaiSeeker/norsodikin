import asyncio
from playwright.async_api import async_playwright

class CodeRenderer:
    async def render(self, code: str, language: str = "auto", theme: str = "dracula", line_numbers: bool = True) -> bytes:
        html_content = self._generate_html(code, language, theme, line_numbers)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=3
            )
            
            page = await context.new_page()
            
            await page.set_content(html_content)
            
            await page.wait_for_load_state("networkidle")
            
            await page.wait_for_selector(".window-container")
            
            element = await page.query_selector(".window-container")
            
            screenshot_bytes = await element.screenshot(omit_background=True)
            
            await browser.close()
            return screenshot_bytes

    def _generate_html(self, code: str, language: str, theme: str, line_numbers: bool) -> str:
        line_numbers_class = "line-numbers" if line_numbers else ""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
            
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/{theme}.min.css">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlightjs-line-numbers.js/2.8.0/highlightjs-line-numbers.min.js"></script>
            
            <style>
                * {{
                    box-sizing: border-box;
                }}
                
                body {{
                    margin: 0;
                    padding: 40px;
                    background-color: transparent;
                    display: inline-flex;
                    justify-content: center;
                    align-items: center;
                }}

                .window-container {{
                    background-color: #282a36;
                    border-radius: 12px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.55);
                    overflow: hidden;
                    min-width: 400px;
                    max-width: 1400px;
                    display: flex;
                    flex-direction: column;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }}

                .window-header {{
                    background: #191A21;
                    padding: 15px 20px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                }}

                .dot {{
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                }}

                .red {{ background-color: #ff5f56; }}
                .yellow {{ background-color: #ffbd2e; }}
                .green {{ background-color: #27c93f; }}

                .title {{
                    flex-grow: 1;
                    text-align: center;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 12px;
                    color: #6272a4;
                    opacity: 0.8;
                }}

                pre {{
                    margin: 0;
                    padding: 20px 25px;
                    overflow: hidden;
                    background: transparent !important;
                }}

                code {{
                    font-family: 'JetBrains Mono', monospace !important;
                    font-size: 16px;
                    line-height: 1.6;
                    tab-size: 4;
                }}

                .hljs-ln-numbers {{
                    -webkit-touch-callout: none;
                    -webkit-user-select: none;
                    -khtml-user-select: none;
                    -moz-user-select: none;
                    -ms-user-select: none;
                    user-select: none;
                    text-align: right;
                    color: #6272a4;
                    border-right: 1px solid rgba(255, 255, 255, 0.1);
                    vertical-align: top;
                    padding-right: 15px !important;
                    margin-right: 15px !important;
                }}

                .hljs-ln-code {{
                    padding-left: 15px !important;
                }}
            </style>
        </head>
        <body>
            <div class="window-container">
                <div class="window-header">
                    <div class="dot red"></div>
                    <div class="dot yellow"></div>
                    <div class="dot green"></div>
                    <div class="title">python</div>
                </div>
                <pre><code class="language-{language} {line_numbers_class}">{code}</code></pre>
            </div>

            <script>
                hljs.highlightAll();
                if ({str(line_numbers).lower()}) {{
                    hljs.initLineNumbersOnLoad();
                }}
            </script>
        </body>
        </html>
        """
