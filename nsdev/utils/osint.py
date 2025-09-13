from types import SimpleNamespace
from typing import List

import asyncio
import httpx


class OsintTools:
    async def get_ip_info(self, ip_or_domain: str) -> SimpleNamespace:
        api_url = f"http://ip-api.com/json/{ip_or_domain}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(api_url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data.get("status") == "fail":
                    raise ValueError(data.get("message", "Invalid query"))
                return SimpleNamespace(**data)
            except httpx.RequestError as e:
                raise Exception(f"Failed to connect to IP API: {e}")
            except (KeyError, ValueError) as e:
                raise ValueError(f"Could not parse IP API response: {e}")

    async def check_username(self, username: str) -> List[dict]:
        PLATFORMS = {
            "Instagram": "https://www.instagram.com/{}",
            "Twitter / X": "https://www.twitter.com/{}",
            "GitHub": "https://www.github.com/{}",
            "TikTok": "https://www.tiktok.com/@{}",
            "YouTube": "https://www.youtube.com/@{}",
            "Facebook": "https://www.facebook.com/{}",
            "Reddit": "https://www.reddit.com/user/{}",
            "Pinterest": "https://www.pinterest.com/{}/",
            "Steam": "https://steamcommunity.com/id/{}",
        }

        async def _check_site(session, url_template, platform_name):
            url = url_template.format(username)
            try:
                response = await session.head(url, allow_redirects=True, timeout=5)
                if 200 <= response.status_code < 300:
                    return {"platform": platform_name, "url": str(response.url)}
            except httpx.RequestError:
                pass
            return None

        async with httpx.AsyncClient() as session:
            tasks = [
                _check_site(session, url, platform)
                for platform, url in PLATFORMS.items()
            ]
            results = await asyncio.gather(*tasks)
            return [res for res in results if res]
