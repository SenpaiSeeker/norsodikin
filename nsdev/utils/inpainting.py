import asyncio
import base64
import time
from functools import partial
from io import BytesIO
from playwright.async_api import async_playwright

class ImageInpainter:
    async def remove_watermark(self, image_bytes: bytes) -> bytes:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            data_uri = f"data:image/jpeg;base64,{image_base64}"

            try:
                await page.goto("https://cleanup.pictures/")
                
                file_input = await page.wait_for_selector('input[type="file"]')
                
                await file_input.set_input_files({
                    "name": "input.jpg",
                    "mimeType": "image/jpeg",
                    "buffer": image_bytes
                })

                await page.wait_for_selector(".canvas-container", state="visible")
                
                canvas_size = await page.evaluate("""() => {
                    const canvas = document.querySelector('.canvas-container canvas');
                    return {width: canvas.width, height: canvas.height};
                }""")
                
                w = canvas_size['width']
                h = canvas_size['height']

                mask_script = f"""
                () => {{
                    const canvas = document.querySelector('.canvas-container canvas');
                    const ctx = canvas.getContext('2d');
                    
                    ctx.globalCompositeOperation = 'destination-out';
                    ctx.beginPath();
                    ctx.lineWidth = 50;
                    ctx.lineCap = 'round';

                    const steps = 10;
                    const corners = [
                        [0, 0, {w*0.3}, {h*0.15}],
                        [{w - (w*0.3)}, {h - (h*0.15)}, {w}, {h}], 
                        [{w - (w*0.3)}, 0, {w}, {h*0.15}],         
                        [0, {h - (h*0.15)}, {w*0.3}, {h}]          
                    ];

                    corners.forEach(c => {{
                        ctx.moveTo(c[0], c[1]);
                        ctx.lineTo(c[2], c[3]);
                        ctx.stroke();
                    }});

                    const event = new MouseEvent('mouseup', {{
                        bubbles: true,
                        cancelable: true,
                        view: window
                    }});
                    canvas.dispatchEvent(event);
                }}
                """
                await page.evaluate(mask_script)

                time.sleep(3)
                await page.wait_for_timeout(3000) 
                
                result_img_element = await page.wait_for_selector('img.output-image', timeout=20000)
                
                if result_img_element:
                    src = await result_img_element.get_attribute('src')
                    if src and "base64" in src:
                        base64_data = src.split(",")[1]
                        return base64.b64decode(base64_data)
                        
                download_button = await page.query_selector('button:has-text("Download")')
                if download_button:
                    async with page.expect_download() as download_info:
                        await download_button.click()
                    
                    download = await download_info.value
                    path = await download.path()
                    with open(path, 'rb') as f:
                        return f.read()

            except Exception as e:
                raise RuntimeError(f"Scraper inpainting gagal: {e}")
            finally:
                await browser.close()
