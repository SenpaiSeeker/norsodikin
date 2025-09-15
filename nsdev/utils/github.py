from types import SimpleNamespace
from urllib.parse import urljoin, urlparse, urlunparse
import datetime

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
                
            except httpx.RequestError as e:
                raise Exception(f"Failed to fetch GitHub API data: {e}")

        created_at_str = user_data.get("created_at", "")
        created_at_dt = None
        if created_at_str:
            try:
                created_at_dt = datetime.datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            except ValueError:
                pass
        
        avatar_url = user_data.get("avatar_url", "")
        if avatar_url:
            parsed_url = urlparse(avatar_url)
            avatar_url = urlunparse(parsed_url._replace(query=""))

        return SimpleNamespace(
            username=user_data.get("login", username),
            name=user_data.get("name"),
            bio=user_data.get("bio"),
            company=user_data.get("company"),
            blog=user_data.get("blog"),
            location=user_data.get("location"),
            email=user_data.get("email"),
            twitter=user_data.get("twitter_username"),
            public_repos=user_data.get("public_repos", 0),
            followers=user_data.get("followers", 0),
            following=user_data.get("following", 0),
            created_at=created_at_dt,
            profile_url=user_data.get("html_url", profile_url),
            avatar_url=avatar_url,
        )
