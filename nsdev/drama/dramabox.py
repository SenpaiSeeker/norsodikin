import requests
from typing import Optional, Dict, Any

class DramaboxAPI:
    def __init__(self, token: str = "715B92C587621A9914F00563A7FB6852", lang: str = "in"):
        self.base_url = "https://dramabox.dramabos.my.id"
        self.token = token
        self.lang = lang
        self.session = requests.Session()

    def homepage(self, page: int = 1) -> Dict[str, Any]:
        params = {"page": str(page), "lang": self.lang}
        response = self.session.get(f"{self.base_url}/api/v1/homepage", params=params)
        return response.json()

    def dubbed(self, classify: str = "terpopuler", page: int = 1) -> Dict[str, Any]:
        params = {"classify": classify, "page": str(page), "lang": self.lang}
        response = self.session.get(f"{self.base_url}/api/v1/dubbed", params=params)
        return response.json()

    def foryou(self) -> Dict[str, Any]:
        params = {"lang": self.lang}
        response = self.session.get(f"{self.base_url}/api/v1/foryou", params=params)
        return response.json()

    def latest(self) -> Dict[str, Any]:
        params = {"lang": self.lang}
        response = self.session.get(f"{self.base_url}/api/v1/latest", params=params)
        return response.json()

    def populersearch(self) -> Dict[str, Any]:
        params = {"lang": self.lang}
        response = self.session.get(f"{self.base_url}/api/v1/populersearch", params=params)
        return response.json()

    def search(self, query: str) -> Dict[str, Any]:
        params = {"query": query, "lang": self.lang}
        response = self.session.get(f"{self.base_url}/api/v1/search", params=params)
        return response.json()

    def detail(self, bookId: str) -> Dict[str, Any]:
        params = {"bookId": bookId, "lang": self.lang, "code": self.token}
        response = self.session.get(f"{self.base_url}/api/v1/detail", params=params)
        return response.json()

    def allepisode(self, bookId: str) -> Dict[str, Any]:
        params = {"bookId": bookId, "code": self.token}
        response = self.session.get(f"{self.base_url}/api/v1/allepisode", params=params)
        return response.json()
