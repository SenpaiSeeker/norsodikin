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
        with open(self.cookies_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def _generate_with_browser(self, prompt: str):
        driver = None
        try:
            options = uc.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            self.__log(f"{self.log.CYAN}Meluncurkan browser headless...")
            driver = uc.Chrome(options=options, version_main=119)
            
            driver.get(self.base_url)
            
            self.__log(f"{self.log.CYAN}Memuat cookies...")
            cookies = self._get_cookies()
            for cookie in cookies:
                if 'domain' in cookie and 'bing.com' in cookie['domain']:
                    driver.add_cookie(cookie)
            
            driver.get(f"{self.base_url}?q={prompt}")
            
            self.__log(f"{self.log.GREEN}Menunggu halaman dimuat dan prompt dikirim...")
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.ID, "create_btn_c"))
            )

            time.sleep(10)

            self.__log(f"{self.log.YELLOW}Menunggu hasil gambar (ini bisa memakan waktu hingga 2 menit)...")
            WebDriverWait(driver, 200).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#gi_cmp_roller.gil_eco_chat.hasspace.gicpr_vrt_sct"))
            )
            
            self.__log(f"{self.log.GREEN}Mengambil URL gambar...")
            image_elements = driver.find_elements(By.CSS_SELECTOR, 'div.img_cont a.iusc img')
            
            image_urls = [re.sub(r'&w=\d+&h=\d+', '&w=1024&h=1024', el.get_attribute('src')) for el in image_elements if el.get_attribute('src')]

            if not image_urls:
                 raise Exception("Tidak ada URL gambar yang ditemukan setelah generasi selesai.")
            
            return list(dict.fromkeys(image_urls))

        finally:
            if driver:
                driver.quit()
                self.__log(f"{self.log.YELLOW}Browser headless ditutup.")

    async def generate(self, prompt: str):
        self.__log(f"{self.log.GREEN}Memulai pembuatan gambar untuk prompt: '{prompt}' menggunakan browser automation.")
        loop = asyncio.get_running_loop()
        image_urls = await loop.run_in_executor(
            None, lambda: asyncio.run(self._generate_with_browser(prompt))
        )
        return image_urls
