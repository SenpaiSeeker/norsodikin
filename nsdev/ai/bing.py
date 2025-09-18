import asyncio
import os
import re
import time
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

    def _run_browser_automation(self, prompt: str):
        driver = None
        try:
            options = uc.ChromeOptions()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            
            self.__log(f"{self.log.CYAN}Meluncurkan browser headless... (Mungkin perlu mengunduh driver yang sesuai)")
            driver = uc.Chrome(options=options, use_subprocess=False)
            
            self.__log(f"{self.log.CYAN}Menavigasi ke Bing dan memuat cookies...")
            driver.get("https://www.bing.com")
            
            cookies = self._get_cookies()
            for cookie in cookies:
                if 'domain' in cookie and 'bing.com' in cookie['domain']:
                    driver.add_cookie(cookie)
            
            encoded_prompt = uc.quote(prompt)
            driver.get(f"{self.base_url}?q={encoded_prompt}&ensearch=1")
            
            self.__log(f"{self.log.GREEN}Menunggu halaman dimuat dan prompt diproses...")

            WebDriverWait(driver, 120).until(
                lambda d: d.find_element(By.ID, "gil_cl") or "action-err" in d.page_source
            )
            
            if "prompt has been blocked" in driver.page_source or "action-err" in driver.page_source:
                 raise Exception("Prompt Anda diblokir oleh kebijakan konten Bing.")

            self.__log(f"{self.log.YELLOW}Menunggu hasil gambar (ini bisa memakan waktu hingga 2 menit)...")
            
            WebDriverWait(driver, 240).until(
                EC.presence_of_element_located((By.ID, "giric"))
            )
            
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div#giric a.iusc img'))
            )
            
            self.__log(f"{self.log.GREEN}Mengambil URL gambar...")
            image_elements = driver.find_elements(By.CSS_SELECTOR, 'div#giric a.iusc img')
            
            image_urls = [re.sub(r'[?&]w=\d+&h=\d+&c=\d+&rs=\d+&qlt=\d+&o=\d+&pid=ImgGn', '', el.get_attribute('src')) for el in image_elements if el.get_attribute('src')]

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
