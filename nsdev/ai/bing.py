import asyncio
import os
import re
import time
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote

from ..utils.logger import LoggerHandler

class ImageGenerator:
    def __init__(self, cookies_file_path: str = "cookies.txt", logging_enabled: bool = True):
        self.cookies_file_path = cookies_file_path
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()
        self.base_url = "https://www.bing.com/images/create"
        
        if not os.path.exists(cookies_file_path):
            raise FileNotFoundError(f"File cookie tidak ditemukan: {cookies_file_path}")

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    def _get_cookies(self):
        try:
            with open(self.cookies_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
             raise ValueError("Format file cookie salah. Harus berupa format JSON yang valid.")

    def _sanitize_cookies(self, cookies):
        sanitized = []
        for cookie in cookies:
            if 'sameSite' in cookie and cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                del cookie['sameSite']
            sanitized.append(cookie)
        return sanitized

    def _run_browser_automation(self, prompt: str):
        driver = None
        try:
            options = uc.ChromeOptions()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            
            self.__log(f"{self.log.CYAN}Meluncurkan browser headless...")
            driver = uc.Chrome(options=options)
            
            self.__log(f"{self.log.CYAN}Menavigasi ke Bing dan memuat cookies...")
            driver.get("https://www.bing.com") 
            
            cookies = self._get_cookies()
            sanitized_cookies = self._sanitize_cookies(cookies)

            for cookie in sanitized_cookies:
                if 'domain' in cookie and 'bing.com' in cookie['domain']:
                    driver.add_cookie(cookie)
            
            encoded_prompt = quote(prompt)
            driver.get(f"{self.base_url}?q={encoded_prompt}&rt=4&FORM=GENCRE")
            
            self.__log(f"{self.log.GREEN}Menunggu halaman dimuat...")
            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "create_btn_c")))

            self.__log(f"{self.log.YELLOW}Memulai generasi gambar (ini bisa memakan waktu hingga 3 menit)...")
            WebDriverWait(driver, 300).until(
                EC.presence_of_element_located((By.ID, "giric"))
            )

            try:
                throttle_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "giloader"))
                )
                self.__log(f"{self.log.YELLOW}Pembuatan gambar mungkin lebih lambat, menunggu... ")
                WebDriverWait(driver, 300).until(
                    EC.invisibility_of_element_located((By.ID, "giloader"))
                )
            except Exception:
                pass

            self.__log(f"{self.log.GREEN}Menunggu gambar muncul di galeri...")
            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div#giric .img_cont img.mimg'))
            )
            
            self.__log(f"{self.log.GREEN}Mengambil URL gambar...")
            image_elements = driver.find_elements(By.CSS_SELECTOR, 'div#giric .img_cont img.mimg')
            
            image_urls = [re.sub(r'[?&]w=\d+&h=\d+.*', '', el.get_attribute('src')) for el in image_elements if el.get_attribute('src')]

            if not image_urls:
                 raise Exception("Tidak ada URL gambar yang ditemukan setelah generasi selesai.")
            
            return list(dict.fromkeys(image_urls))

        finally:
            if driver:
                driver.quit()
                self.__log(f"{self.log.YELLOW}Browser headless ditutup.")

    async def generate(self, prompt: str):
        self.__log(f"{self.log.GREEN}Memulai pembuatan gambar untuk prompt: '{prompt}'")
        loop = asyncio.get_running_loop()
        try:
            image_urls = await loop.run_in_executor(
                None, self._run_browser_automation, prompt
            )
            return image_urls
        except Exception as e:
            self.__log(f"{self.log.RED}Terjadi kesalahan selama otomasi browser: {e}")
            raise e
