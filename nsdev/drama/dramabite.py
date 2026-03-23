import requests
from typing import Optional, Dict, Any

class DramaBiteAPI:
    def __init__(self, token: str = "715B92C587621A9914F00563A7FB6852", lang: str = "id"):
        self.base_url = "https://dramabite.dramabos.my.id"
        self.token = token
        self.lang = lang
        self.session = requests.Session()

    def languages(self) -> Dict[str, Any]:
        response = self.session.get(f"{self.base_url}/languages")
        return response.json()

    def home(self) -> Dict[str, Any]:
        params = {"lang": self.lang}
        response = self.session.get(f"{self.base_url}/home", params=params)
        return response.json()

    def module(self, page: int = 1) -> Dict[str, Any]:
        params = {"page": str(page), "lang": self.lang}
        response = self.session.get(f"{self.base_url}/module", params=params)
        return response.json()

    def search(self, query: str) -> Dict[str, Any]:
        params = {"q": query, "lang": self.lang}
        response = self.session.get(f"{self.base_url}/search", params=params)
        return response.json()

    def detail(self, cid: str) -> Dict[str, Any]:
        params = {"cid": cid, "lang": self.lang}
        response = self.session.get(f"{self.base_url}/drama/{cid}", params=params)
        return response.json()

    def episodes(self, cid: str) -> Dict[str, Any]:
        params = {"cid": cid, "lang": self.lang, "code": self.token}
        response = self.session.get(f"{self.base_url}/episodes/{cid}", params=params)
        return response.json()

    def play(self, cid: str, vid: str) -> Dict[str, Any]:
        params = {"cid": cid, "vid": vid, "lang": self.lang, "code": self.token}
        response = self.session.get(f"{self.base_url}/play/{cid}/{vid}", params=params)
        return response.json()
