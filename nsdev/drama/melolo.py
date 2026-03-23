import requests
from typing import Optional, Dict, Any

class MeloloAPI:
    def __init__(self, token: str, lang: str = "id"):
        self.base_url = "https://melolo.dramabos.my.id"
        self.token = token
        self.lang = lang
        self.session = requests.Session()

    def home(self, offset: int = 0) -> Dict[str, Any]:
        params = {"lang": self.lang, "offset": str(offset)}
        response = self.session.get(f"{self.base_url}/api/home", params=params)
        return response.json()

    def detail(self, drama_id: str) -> Dict[str, Any]:
        params = {"id": drama_id, "lang": self.lang}
        response = self.session.get(f"{self.base_url}/api/detail/{drama_id}", params=params)
        return response.json()

    def search(self, query: str) -> Dict[str, Any]:
        params = {"lang": self.lang, "q": query}
        response = self.session.get(f"{self.base_url}/api/search", params=params)
        return response.json()

    def video(self, vid: str) -> Dict[str, Any]:
        params = {"vid": vid, "lang": self.lang, "code": self.token}
        response = self.session.get(f"{self.base_url}/api/video/{vid}", params=params)
        return response.json()
