import json
import re
import time
import requests
from urllib.parse import quote_plus, unquote_plus, urlencode
from .models import PinterestMedia

class Endpoint:
    _BASE = "https://www.pinterest.com"
    GET_RELATED_MODULES = f"{_BASE}/resource/RelatedModulesResource/get/"
    GET_MAIN_IMAGE = f"{_BASE}/resource/ApiResource/get/"
    GET_BOARD_RESOURCE = f"{_BASE}/resource/BoardResource/get/"
    GET_BOARD_FEED_RESOURCE = f"{_BASE}/resource/BoardFeedResource/get/"
    GET_SEARCH_RESOURCE = f"{_BASE}/resource/BaseSearchResource/get/"

class RequestBuilder:
    @staticmethod
    def build_post(options, source_url="/", context=None) -> str:
        return RequestBuilder.url_encode(
            {
                "source_url": source_url,
                "data": json.dumps({"options": options, "context": context}),
                "_": "%s" % int(time.time() * 1000),
            }
        )

    @staticmethod
    def build_get(endpoint: str, options: dict, source_url: str = "/", context: dict = {}) -> str:
        query = RequestBuilder.url_encode(
            {
                "source_url": source_url,
                "data": json.dumps({"options": options, "context": context}),
                "_": "%s" % int(time.time() * 1000),
            }
        )
        url = f"{endpoint}?{query}"
        return url

    @staticmethod
    def url_encode(query: str | dict) -> str:
        if isinstance(query, str):
            query = quote_plus(query)
        else:
            query = urlencode(query)
        query = query.replace("+", "%20")
        return query

    @staticmethod
    def url_decode(query: str) -> str:
        return unquote_plus(query)

class PinterestAPI:
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
    )

    def __init__(self, timeout: float = 10) -> None:
        self.timeout = timeout
        self.endpoint = Endpoint()
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self.USER_AGENT})
        self._session.headers.update(
            {"x-pinterest-pws-handler": "www/pin/[id].js"}
        )
        self._init_cookies()

    def _init_cookies(self):
        try:
            self._session.get(self.endpoint._BASE, timeout=self.timeout)
        except Exception:
            pass

    def _parse_search_query(self, url: str) -> str:
        result = re.search(r"/search/pins/\?q=([A-Za-z0-9%]+)", url)
        if not result:
            return None
        query = result.group(1)
        return RequestBuilder.url_decode(query)

    def get_search(self, query: str, num: int, bookmark: str = None) -> dict:
        source_url = f"/search/pins/?q={query}&rs=typed"
        endpoint = self.endpoint.GET_SEARCH_RESOURCE
        options = {
            "appliedProductFilters": "---",
            "auto_correction_disabled": False,
            "bookmarks": [bookmark] if bookmark else [],
            "page_size": num,
            "query": query,
            "redux_normalize_feed": True,
            "rs": "typed",
            "scope": "pins",
            "source_url": source_url,
        }

        try:
            request_url = RequestBuilder.build_get(endpoint, options, source_url)
            response_raw = self._session.get(request_url, timeout=self.timeout)
            return response_raw.json()
        except Exception as e:
            raise Exception(f"Failed to request search: {e}")

    def get_related_images(self, pin_id: str, num: int, bookmark: str = None) -> dict:
        endpoint = self.endpoint.GET_RELATED_MODULES
        source_url = f"/pin/{pin_id}/"
        options = {
            "pin_id": f"{pin_id}",
            "context_pin_ids": [],
            "page_size": num,
            "bookmarks": [bookmark] if bookmark else [],
            "search_query": "",
            "source": "deep_linking",
            "top_level_source": "deep_linking",
            "top_level_source_depth": 1,
            "is_pdp": False,
        }
        try:
            request_url = RequestBuilder.build_get(endpoint, options, source_url)
            response_raw = self._session.get(request_url, timeout=self.timeout)
            return response_raw.json()
        except Exception as e:
            raise Exception(f"Failed to request related images: {e}")
