from types import SimpleNamespace
from urllib.parse import urljoin

import bs4
import fake_useragent
import httpx


class GitHubInfo:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.base_url = "https://github.com"
        self.headers = {"User-Agent": fake_useragent.UserAgent().random}

    async def get_user_info(self, username: str) -> SimpleNamespace:
        profile_url = urljoin(self.base_url, username)

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                response = await client.get(profile_url, headers=self.headers, timeout=self.timeout)
                if response.status_code == 404:
                    raise ValueError(f"User '{username}' not found.")
                response.raise_for_status()
            except httpx.RequestError as e:
                raise Exception(f"Failed to fetch GitHub profile: {e}")

        soup = bs4.BeautifulSoup(response.text, "lxml")

        name_tag = soup.find("span", class_="p-name")
        name = name_tag.get_text(strip=True) if name_tag else "N/A"

        bio_tag = soup.find("div", class_="p-note")
        bio = bio_tag.get_text(strip=True) if bio_tag else "No bio available."

        followers_tag = soup.find("a", href=f"/{username}?tab=followers")
        followers = followers_tag.find("span", class_="text-bold").get_text(strip=True) if followers_tag else "0"

        following_tag = soup.find("a", href=f"/{username}?tab=following")
        following = following_tag.find("span", class_="text-bold").get_text(strip=True) if following_tag else "0"

        avatar_tag = soup.find("img", class_="avatar-user")
        avatar_url = avatar_tag["src"] if avatar_tag else ""

        pinned_repos_tags = soup.find_all("li", class_="pinned-item-list-item-public")
        pinned_repos = []
        for repo_tag in pinned_repos_tags:
            repo_name_tag = repo_tag.find("span", class_="repo")
            repo_desc_tag = repo_tag.find("p", class_="pinned-item-desc")
            repo_lang_tag = repo_tag.find("span", {"itemprop": "programmingLanguage"})
            repo_stars_tag = repo_tag.find("a", href=lambda href: href and "stargazers" in href)

            pinned_repos.append(
                SimpleNamespace(
                    name=repo_name_tag.get_text(strip=True) if repo_name_tag else "N/A",
                    description=repo_desc_tag.get_text(strip=True) if repo_desc_tag else "",
                    language=repo_lang_tag.get_text(strip=True) if repo_lang_tag else "N/A",
                    stars=repo_stars_tag.get_text(strip=True) if repo_stars_tag else "0",
                )
            )

        return SimpleNamespace(
            username=username,
            name=name,
            bio=bio,
            followers=followers,
            following=following,
            avatar_url=avatar_url,
            profile_url=profile_url,
            pinned_repos=pinned_repos,
          )
