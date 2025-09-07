from types import SimpleNamespace
from typing import List
from urllib.parse import quote_plus

import bs4
import fake_useragent
import httpx


class WebSearch:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {"User-Agent": fake_useragent.UserAgent().random}

    async def query(self, query: str, num_results: int = 5) -> List[SimpleNamespace]:
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                response = await client.get(search_url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
            except httpx.RequestError as e:
                raise Exception(f"Failed to fetch search results: {e}")

            soup = bs4.BeautifulSoup(response.text, "lxml")
            results_container = soup.find(id="links")
            if not results_container:
                return []

            raw_results = results_container.find_all("div", class_="result", limit=num_results)

            parsed_results = []
            for res in raw_results:
                title_tag = res.find("a", class_="result__a")
                snippet_tag = res.find("a", class_="result__snippet")
                url_tag = title_tag

                if title_tag and snippet_tag and url_tag:
                    title = title_tag.get_text(strip=True)
                    snippet = snippet_tag.get_text(strip=True)
                    url = url_tag.get("href", "")

                    if url:
                        parsed_results.append(SimpleNamespace(title=title, snippet=snippet, url=url))

            return parsed_results
