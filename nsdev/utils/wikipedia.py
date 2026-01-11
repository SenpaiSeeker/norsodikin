import aiohttp
from typing import List, Optional
from fake_useragent import UserAgent

class WikipediaSearch:
    def __init__(self, user_agent: Optional[str] = None):
        self.api_url = "https://id.wikipedia.org/w/api.php"
        self.commons_api_url = "https://commons.wikimedia.org/w/api.php"
        self.ua = UserAgent()
        self.headers = {
            "User-Agent": user_agent or self.ua.random
        }

    async def search(self, query: str, limit: int = 3) -> List:
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "prop": "info|extracts|pageimages",
            "inprop": "url",
            "exintro": True,
            "explaintext": True,
            "piprop": "original",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url, params=params, headers=self.headers) as response:
                data = await response.json()
                
                results = []
                if "query" in data and "search" in data["query"]:
                    search_results = data["query"]["search"]
                    
                    page_ids = [str(item["pageid"]) for item in search_results]
                    details = await self._get_page_details(session, page_ids)
                    
                    for item in search_results:
                        page_id = str(item["pageid"])
                        if page_id in details:
                            detail = details[page_id]
                            
                            image_url = None
                            if "original" in detail:
                                image_url = detail["original"]["source"]
                            
                            results.append(type("WikiResult", (object,), {
                                "title": item["title"],
                                "summary": detail.get("extract", "No summary available."),
                                "url": detail.get("fullurl", ""),
                                "image_url": image_url
                            }))
                            
                return results

    async def _get_page_details(self, session, page_ids):
        params = {
            "action": "query",
            "format": "json",
            "pageids": "|".join(page_ids),
            "prop": "info|extracts|pageimages",
            "inprop": "url",
            "exintro": True,
            "explaintext": True,
            "piprop": "original",
        }
        
        async with session.get(self.api_url, params=params, headers=self.headers) as response:
            data = await response.json()
            if "query" in data and "pages" in data["query"]:
                return data["query"]["pages"]
            return {}

    async def search_image(self, query: str, limit: int = 1) -> List[str]:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6, 
            "iiprop": "url",
            "prop": "imageinfo",
            "format": "json",
            "gsrlimit": limit
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.commons_api_url, params=params, headers=self.headers) as response:
                data = await response.json()
                
                image_urls = []
                if "query" in data and "pages" in data["query"]:
                    pages = data["query"]["pages"]
                    for page_id in pages:
                        page = pages[page_id]
                        if "imageinfo" in page:
                            for info in page["imageinfo"]:
                                if "url" in info:
                                    image_urls.append(info["url"])
                                    
                return image_urls
