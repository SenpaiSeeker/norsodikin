import asyncio
import socket
from types import SimpleNamespace
from typing import List

import httpx


class OsintTools:
    async def get_ip_info(self, ip_or_domain: str) -> SimpleNamespace:
        target = ip_or_domain.strip()

        def _is_ip(s):
            parts = s.split(".")
            return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)

        if not _is_ip(target):
            try:
                loop = asyncio.get_running_loop()
                target = await loop.run_in_executor(None, socket.gethostbyname, target)
            except socket.gaierror:
                raise ValueError(f"Could not resolve domain: {ip_or_domain}")

        api_url = f"https://ipwho.is/{target}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(api_url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data.get("success") is False:
                    raise ValueError(data.get("message", "Invalid query"))

                connection_data = data.get("connection", {})
                timezone_data = data.get("timezone", {})

                result_data = {
                    "ip": data.get("ip"),
                    "country": data.get("country"),
                    "country_code": data.get("country_code"),
                    "region": data.get("region"),
                    "city": data.get("city"),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                    "isp": connection_data.get("isp"),
                    "org": connection_data.get("org"),
                    "asn": connection_data.get("asn"),
                    "timezone_utc": timezone_data.get("utc"),
                }
                return SimpleNamespace(**result_data)

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
                response = await session.head(url, timeout=5)
                if 200 <= response.status_code < 300:
                    return {"platform": platform_name, "url": str(response.url)}
            except httpx.RequestError:
                pass
            return None

        async with httpx.AsyncClient(follow_redirects=True) as session:
            tasks = [_check_site(session, url, platform) for platform, url in PLATFORMS.items()]
            results = await asyncio.gather(*tasks)
            return [res for res in results if res]
