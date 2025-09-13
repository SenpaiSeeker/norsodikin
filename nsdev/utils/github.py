from types import SimpleNamespace
from urllib.parse import urljoin, urlparse, urlunparse

import bs4
import fake_useragent
import httpx


class GitHubInfo:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.base_url = "https://github.com"
        self.api_base_url = "https://api.github.com"
        self.headers = {"User-Agent": fake_useragent.UserAgent().random}

    async def get_user_info(self, username: str) -> SimpleNamespace:
        api_url = f"{self.api_base_url}/users/{username}"
        profile_url = urljoin(self.base_url, username)

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                api_response = await client.get(api_url, headers=self.headers, timeout=self.timeout)
                if api_response.status_code == 404:
                    raise ValueError(f"User '{username}' not found.")
                api_response.raise_for_status()
                user_data = api_response.json()

                html_response = await client.get(profile_url, headers=self.headers, timeout=self.timeout)
                html_response.raise_for_status()

            except httpx.RequestError as e:
                raise Exception(f"Failed to fetch GitHub data: {e}")

        name = user_data.get("name") or username
        bio = user_data.get("bio") or "No bio available."
        followers = user_data.get("followers", 0)
        following = user_data.get("following", 0)
        
        avatar_url = user_data.get("avatar_url", "")
        if avatar_url:
            parsed_url = urlparse(avatar_url)
            avatar_url = urlunparse(parsed_url._replace(query=""))

        soup = bs4.BeautifulSoup(html_response.text, "lxml")
        pinned_repos_tags = soup.select("ol.js-pinned-items-reorder-list li")
        pinned_repos = []

        for repo_tag in pinned_repos_tags:
            repo_name_tag = repo_tag.select_one("span.repo")
            repo_desc_tag = repo_tag.select_one("p.pinned-item-desc")
            repo_lang_tag = repo_tag.select_one("span[itemprop='programmingLanguage']")
            repo_stars_tag = repo_tag.select_one("a[href$='/stargazers']")

            pinned_repos.append(
                SimpleNamespace(
                    name=repo_name_tag.get_text(strip=True) if repo_name_tag else "N/A",
                    description=repo_desc_tag.get_text(strip=True) if repo_desc_tag else "",
                    language=repo_lang_tag.get_text(strip=True) if repo_lang_tag else "N/A",
                    stars=repo_stars_tag.get_text(strip=True).strip() if repo_stars_tag else "0",
                )
            )

        return SimpleNamespace(
            username=user_data.get("login", username),
            name=name,
            bio=bio,
            followers=str(followers),
            following=str(following),
            avatar_url=avatar_url,
            profile_url=user_data.get("html_url", profile_url),
            pinned_repos=pinned_repos,
        )
