import asyncio
import json
import re
from typing import List
import cloudscraper25 as cloudscraper
from bs4 import BeautifulSoup

class Pinterest:
    def __init__(self):
        self.base_search_url = "https://www.pinterest.com/search/pins/"
        self.scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'linux', 'desktop': True})

    async def search(self, query: str, limit: int = 9) -> List[str]:
        unique_urls = set()
        formatted_query = query.replace(" ", "%20")
        url = f"{self.base_search_url}?q={formatted_query}&rs=typed"

        def _fetch(target_url):
            return self.scraper.get(target_url, timeout=30)

        for page in range(1, 4):
            if len(unique_urls) >= limit:
                break

            try:
                response = await asyncio.to_thread(_fetch, url)
                
                if response.status_code != 200:
                    continue

                html_text = response.text
                soup = BeautifulSoup(html_text, "html.parser")
                
                data_scripts = soup.find_all("script", {"id": "__PWS_DATA__"})
                for script in data_scripts:
                    try:
                        json_data = json.loads(script.string)
                        self._extract_from_pws_data(json_data, unique_urls)
                    except Exception:
                        pass

                regex_pattern = r'https://i\.pinimg\.com/(?:\d+x|originals)/[a-z0-9/]+\.(?:jpg|jpeg|png|webp)'
                raw_urls = re.findall(regex_pattern, html_text)
                
                for img_url in raw_urls:
                    if len(unique_urls) >= limit:
                        break
                    
                    if "75x75" in img_url or "32x32" in img_url:
                        continue

                    hd_url = re.sub(r'/\d+x/', '/originals/', img_url)
                    unique_urls.add(hd_url)

            except Exception:
                continue

            await asyncio.sleep(0.5)

        final_list = list(unique_urls)[:limit]
        
        if not final_list:
            raise ValueError(f"Tidak ditemukan gambar untuk query: '{query}'. Pinterest mungkin membatasi akses tanpa login.")
            
        return final_list

    def _extract_from_pws_data(self, data, url_set):
        if isinstance(data, dict):
            if 'images' in data:
                images = data['images']
                target = images.get('originals') or images.get('orig') or images.get('736x')
                if target and 'url' in target:
                    url_set.add(target['url'])
            
            for k, v in data.items():
                self._extract_from_pws_data(v, url_set)
                
        elif isinstance(data, list):
            for item in data:
                self._extract_from_pws_data(item, url_set)

    async def get_image_bytes(self, url: str) -> bytes:
        def _download(target_url):
            return self.scraper.get(target_url, timeout=30)

        try:
            response = await asyncio.to_thread(_download, url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise Exception(f"Error downloading image: {e}")
