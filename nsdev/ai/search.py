from types import SimpleNamespace
from typing import List
from urllib.parse import quote_plus

import bs4
import httpx


class WebSearch:
    def __init__(self, timeout: int = 10):
        self.timeout = httpx.Timeout(timeout)

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def query(self, query: str, num_results: int = 5) -> List[SimpleNamespace]:
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

        async with httpx.AsyncClient(follow_redirects=True, timeout=self.timeout, http2=True) as client:
            try:
                response = await client.get(search_url, headers=self.headers)
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise RuntimeError(f"Failed to fetch search results: {e}") from e

        soup = bs4.BeautifulSoup(response.text, "lxml")
        raw_results = soup.select("div.result")[:num_results]

        parsed_results: List[SimpleNamespace] = []

        for res in raw_results:
            title_tag = res.select_one("a.result__a")
            snippet_tag = (
                res.select_one("div.result__snippet")
                or res.select_one("a.result__snippet")
            )

            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            url = title_tag.get("href", "")

            snippet = ""
            if snippet_tag:
                snippet = snippet_tag.get_text(strip=True)

            if url:
                parsed_results.append(SimpleNamespace(title=title, snippet=snippet, url=url))

        return parsed_results
