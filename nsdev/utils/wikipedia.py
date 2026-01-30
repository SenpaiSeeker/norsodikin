from types import SimpleNamespace
from typing import List
from urllib.parse import quote

import fake_useragent
import httpx


class WikipediaSearch:
    def __init__(self, lang: str = "id", timeout: int = 15):
        self.lang = lang
        self.api_url = f"https://{lang}.wikipedia.org/w/api.php"
        self.commons_url = "https://commons.wikimedia.org/w/api.php"
        self.timeout = timeout
        self.headers = {"User-Agent": fake_useragent.UserAgent().random}

    async def search(self, query: str, limit: int = 1) -> List[SimpleNamespace]:
        if limit == 1:
            return [await self._get_top_article(query)]

        return await self._get_search_list(query, limit)

    async def _get_search_list(self, query: str, limit: int) -> List[SimpleNamespace]:
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "srprop": "snippet",
        }
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                search_response = await client.get(self.api_url, params=search_params, headers=self.headers)
                search_response.raise_for_status()
                search_data = search_response.json()

                results = []
                for item in search_data.get("query", {}).get("search", []):
                    snippet = item.get("snippet", "").replace('<span class="searchmatch">', "").replace("</span>", "")
                    results.append(
                        SimpleNamespace(
                            title=item.get("title"),
                            summary=snippet + "...",
                            url=f"https://{self.lang}.wikipedia.org/wiki/{quote(item.get('title'))}",
                        )
                    )
                return results
            except httpx.HTTPStatusError as e:
                raise Exception(f"Wikipedia API Error ({e.response.status_code}): {e.response.text}")
            except httpx.RequestError as e:
                raise Exception(f"Gagal terhubung ke Wikipedia API: {e}")

    async def _get_top_article(self, query: str) -> SimpleNamespace:
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": 1,
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                search_response = await client.get(self.api_url, params=search_params, headers=self.headers)
                search_response.raise_for_status()
                search_data = search_response.json()

                if not search_data.get("query", {}).get("search"):
                    raise ValueError(f"Tidak ada artikel Wikipedia ditemukan untuk '{query}'.")

                page_title = search_data["query"]["search"][0]["title"]

                summary_params = {
                    "action": "query",
                    "format": "json",
                    "titles": page_title,
                    "prop": "extracts|pageimages",
                    "exintro": True,
                    "explaintext": True,
                    "pithumbsize": 500,
                }
                summary_response = await client.get(self.api_url, params=summary_params, headers=self.headers)
                summary_response.raise_for_status()
                summary_data = summary_response.json()

                pages = summary_data.get("query", {}).get("pages", {})
                if not pages:
                    raise ValueError(f"Gagal mengambil detail halaman untuk '{page_title}'.")

                page = next(iter(pages.values()))

                summary = page.get("extract")
                if not summary or "may refer to" in summary or "dapat mengacu pada" in summary.lower():
                    raise ValueError(f"'{query}' ambigu atau tidak memiliki ringkasan yang jelas.")

                summary = " ".join(summary.split("\n")[0].split()[:60]) + "..."

                image_url = page.get("thumbnail", {}).get("source")
                page_url = f"https://{self.lang}.wikipedia.org/wiki/{quote(page_title)}"

                return SimpleNamespace(
                    title=page.get("title"),
                    summary=summary,
                    url=page_url,
                    image_url=image_url,
                )

            except httpx.HTTPStatusError as e:
                raise Exception(f"Wikipedia API Error ({e.response.status_code}): {e.response.text}")
            except httpx.RequestError as e:
                raise Exception(f"Gagal terhubung ke Wikipedia API: {e}")

    async def search_image(self, query: str, limit: int = 5) -> List[SimpleNamespace]:
        search_params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "iiprop": "url",
            "prop": "imageinfo",
            "format": "json",
            "gsrlimit": limit,
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.get(self.commons_url, params=search_params, headers=self.headers)
                response.raise_for_status()
                data = response.json()

                pages = data.get("query", {}).get("pages", {})
                if not pages:
                    return []

                results = []
                for page in pages.values():
                    image_info = page.get("imageinfo", [])
                    if image_info:
                        img_data = image_info[0]
                        results.append(
                            SimpleNamespace(
                                title=page.get("title", "").replace("File:", "").replace("Berkas:", ""),
                                image_url=img_data.get("url"),
                                description_url=img_data.get("descriptionurl"),
                            )
                        )
                return results

            except httpx.HTTPStatusError as e:
                raise Exception(f"Wikimedia Commons API Error ({e.response.status_code}): {e.response.text}")
            except httpx.RequestError as e:
                raise Exception(f"Gagal terhubung ke Wikimedia Commons API: {e}")
