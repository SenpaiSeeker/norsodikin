from types import SimpleNamespace
import httpx

class TMDbClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.img_base_url = "https://image.tmdb.org/t/p/w500"

    async def _get_trailer_link(self, client, item_id, media_type):
        video_url = f"{self.base_url}/{media_type}/{item_id}/videos"
        params = {"api_key": self.api_key}
        try:
            res = await client.get(video_url, params=params)
            res.raise_for_status()
            videos = res.json().get("results", [])
            for video in videos:
                if video["site"] == "YouTube" and video["type"] == "Trailer":
                    return f"https://www.youtube.com/watch?v={video['key']}"
        except httpx.RequestError:
            return None
        return None

    async def search(self, query: str, media_type: str = "movie") -> SimpleNamespace:
        search_url = f"{self.base_url}/search/{media_type}"
        params = {"api_key": self.api_key, "query": query, "language": "id-ID"}

        async with httpx.AsyncClient(timeout=20) as client:
            try:
                search_res = await client.get(search_url, params=params)
                search_res.raise_for_status()
                search_data = search_res.json()
                if not search_data.get("results"):
                    raise ValueError(f"Tidak ada hasil ditemukan untuk '{query}'.")

                best_result = search_data["results"][0]
                item_id = best_result["id"]

                detail_url = f"{self.base_url}/{media_type}/{item_id}"
                detail_res = await client.get(detail_url, params={"api_key": self.api_key, "language": "id-ID"})
                detail_res.raise_for_status()
                details = detail_res.json()

                trailer_link = await self._get_trailer_link(client, item_id, media_type)

                return SimpleNamespace(
                    title=details.get("title") or details.get("name"),
                    release_year=(details.get("release_date") or details.get("first_air_date", "N/A"))[:4],
                    rating=details.get("vote_average"),
                    genres=[g["name"] for g in details.get("genres", [])],
                    overview=details.get("overview", "Tidak ada plot."),
                    poster_url=f"{self.img_base_url}{details['poster_path']}" if details.get("poster_path") else None,
                    imdb_url=f"https://www.imdb.com/title/{details['imdb_id']}" if details.get("imdb_id") else None,
                    trailer_url=trailer_link
                )

            except httpx.RequestError as e:
                raise Exception(f"Gagal menghubungi API TMDb: {e}")
