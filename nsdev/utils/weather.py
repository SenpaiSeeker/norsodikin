from urllib.parse import quote
import httpx

class WeatherWttr:
    async def get_weather_image(self, city: str) -> bytes:
        encoded_city = quote(city)
        url = f"https://wttr.in/{encoded_city}.png?m&lang=id&0"

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                response = await client.get(url, timeout=20)

                if response.status_code != 200:
                    raise ValueError(f"Kota '{city}' tidak ditemukan atau layanan tidak tersedia.")
                
                content_type = response.headers.get("content-type", "")
                if "image/png" not in content_type:
                    raise ValueError(f"Kota '{city}' tidak ditemukan oleh layanan cuaca.")

                return response.content

            except httpx.RequestError as e:
                raise Exception(f"Gagal menghubungi layanan cuaca: {e}")
