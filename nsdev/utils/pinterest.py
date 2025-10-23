import asyncio
from types import SimpleNamespace
from typing import List

import httpx

from ..data.ymlreder import YamlHandler


class PinterestAPI:
    def __init__(self):
        self.base_url = "https://api.siputzx.my.id/api/s/pinterest"
        self.convert = YamlHandler()
        self.headers = {
            "accept": "*/*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    async def search(self, query: str, type: str = "image") -> SimpleNamespace:
        params = {"query": query, "type": type}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                json_data = response.json()

            loop = asyncio.get_running_loop()
            parsed_response = await loop.run_in_executor(None, self._parse_response, json_data)
            return parsed_response

        except httpx.RequestError as e:
            raise Exception(f"Pinterest API error: {e}")
        except Exception as e:
            raise Exception(f"An error occurred: {e}")

    def _parse_response(self, json_data: dict) -> SimpleNamespace:
        return self.convert._convertToNamespace(json_data)

    def filter_by_type(self, items: List[SimpleNamespace], type: str) -> List[SimpleNamespace]:
        return [item for item in items if hasattr(item, "type") and item.type == type]

    def sort_by_reactions(self, items: List[SimpleNamespace], ascending: bool = False) -> List[SimpleNamespace]:
        def get_total_reactions(item):
            return sum(item.reaction_counts.__dict__.values()) if hasattr(item, "reaction_counts") else 0

        return sorted(items, key=get_total_reactions, reverse=not ascending)

    def get_image_urls(self, items: List[SimpleNamespace]) -> List[str]:
        return [item.image_url for item in items if hasattr(item, "image_url") and item.image_url]

    def get_video_urls(self, items: List[SimpleNamespace]) -> List[str]:
        return [item.video_url for item in items if hasattr(item, "video_url") and item.video_url]
