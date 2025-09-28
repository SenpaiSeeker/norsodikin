from types import SimpleNamespace
from typing import List
from urllib.parse import quote

import httpx


class WikipediaSearch:
    def __init__(self, lang: str = "id", timeout: int = 15):
        self.api_url = f"https://{lang}.wikipedia.org/w/api.php"
        self.timeout = timeout

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
        async with httpx.AsyncClient() as client:
            try:
                search_response = await client.get(self.api_url, params=search_params, timeout=self.timeout)
                search_response.raise_for_status()
                search_data = search_response.json()

                results = []
                for item in search_data.get("query", {}).get("search", []):
                    snippet = item.get("snippet", "").replace('<span class="searchmatch">', "").replace("</span>", "")
                    results.append(
                        SimpleNamespace(
                            title=item.get("title"),
                            summary=snippet + "...",
                            url=f"https://id.wikipedia.org/wiki/{quote(item.get('title'))}",
                        )
                    )
                return results
            except httpx.RequestError as e:
                raise Exception(f"Failed to connect to Wikipedia API: {e}")

    async def _get_top_article(self, query: str) -> SimpleNamespace:
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": 1,
        }

        async with httpx.AsyncClient() as client:
            try:
                search_response = await client.get(self.api_url, params=search_params, timeout=self.timeout)
                search_response.raise_for_status()
                search_data = search_response.json()

                if not search_data["query"]["search"]:
                    raise ValueError(f"No Wikipedia article found for '{query}'.")

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
                summary_response = await client.get(self.api_url, params=summary_params, timeout=self.timeout)
                summary_response.raise_for_status()
                summary_data = summary_response.json()
                page = next(iter(summary_data["query"]["pages"].values()))

                summary = page.get("extract")
                if not summary or "may refer to" in summary:
                    raise ValueError(f"'{query}' is ambiguous or has no summary.")

                summary = " ".join(summary.split("\n")[0].split()[:60]) + "..."

                image_url = page.get("thumbnail", {}).get("source")
                page_url = f"https://id.wikipedia.org/wiki/{quote(page_title)}"

                return SimpleNamespace(
                    title=page.get("title"),
                    summary=summary,
                    url=page_url,
                    image_url=image_url,
                )

            except httpx.RequestError as e:
                raise Exception(f"Failed to connect to Wikipedia API: {e}")
