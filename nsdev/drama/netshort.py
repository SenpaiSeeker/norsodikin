import requests
from typing import Optional, Dict, Any

class NetShortAPI:
    def __init__(self, token: str, lang: str = "in"):
        self.base_url = "https://netshort.dramabos.my.id"
        self.token = token
        self.lang = lang
        self.session = requests.Session()

    def home(self, page: int = 1) -> Dict[str, Any]:
        params = {"lang": self.lang}
        response = self.session.get(f"{self.base_url}/api/home/{page}", params=params)
        return response.json()

    def categories(self) -> Dict[str, Any]:
        params = {"lang": self.lang}
        response = self.session.get(f"{self.base_url}/api/categories", params=params)
        return response.json()

    def list_drama(self, page: int = 1, region: Optional[str] = None, audio: Optional[str] = None, tag: Optional[str] = None, sort: Optional[str] = None) -> Dict[str, Any]:
        params = {"lang": self.lang}
        if region:
            params["region"] = region
        if audio:
            params["audio"] = audio
        if tag:
            params["tag"] = tag
        if sort:
            params["sort"] = sort
        response = self.session.get(f"{self.base_url}/api/list/{page}", params=params)
        return response.json()

    def detail(self, drama_id: str) -> Dict[str, Any]:
        params = {"id": drama_id, "lang": self.lang}
        response = self.session.get(f"{self.base_url}/api/drama/{drama_id}", params=params)
        return response.json()

    def watch(self, drama_id: str, episode: int = 1) -> Dict[str, Any]:
        params = {"id": drama_id, "ep": str(episode), "lang": self.lang, "code": self.token}
        response = self.session.get(f"{self.base_url}/api/watch/{drama_id}/{episode}", params=params)
        return response.json()

    def search(self, query: str, page: int = 1) -> Dict[str, Any]:
        params = {"lang": self.lang, "q": query, "page": str(page)}
        response = self.session.get(f"{self.base_url}/api/search", params=params)
        return response.json()
