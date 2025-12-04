import asyncio
import base64
import re
from playwright.async_api import async_playwright

class ImageInpainter:
    async def remove_watermark(self, image_bytes: bytes) -> bytes:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                await page.goto("https://www.watermarkremover.io/", wait_until="networkidle", timeout=60000)
                
                file_input = await page.wait_for_selector('input[type="file"]', state="attached")
                await file_input.set_input_files({
                    "name": "input_image.jpg",
                    "mimeType": "image/jpeg",
                    "buffer": image_bytes
                })

                await page.wait_for_selector("div[class*='TransformImage_processedImage']", timeout=60000)
                await asyncio.sleep(2)

                img_elements = await page.query_selector_all("img")
                result_url = None
                
                for img in img_elements:
                    src = await img.get_attribute("src")
                    if src and "cloudfront.net" in src and "a.png" not in src: 
                        if src.startswith("http"):
                             result_url = src
                             break
                
                if not result_url:
                    raise Exception("Gagal menemukan gambar hasil (processed image).")
                
                response = await page.request.get(result_url)
                if response.status != 200:
                     raise Exception("Gagal mengunduh gambar hasil dari URL.")
                     
                return await response.body()

            except Exception as e:
                raise RuntimeError(f"Scraper watermarkremover.io gagal: {e}")
            finally:
                await browser.close()
