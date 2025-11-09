import asyncio

import httpx

from ..utils.logger import LoggerHandler


class AnimeStyleConverter:
    def __init__(self, api_key: str, model_id: str = "akhaliq/Photo-to-Anime"):
        self.api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.client = httpx.AsyncClient(headers=self.headers, timeout=300)
        self.log = LoggerHandler()

    async def convert(self, image_bytes: bytes, max_retries: int = 5, initial_delay: int = 10) -> bytes:
        for attempt in range(max_retries):
            try:
                response = await self.client.post(self.api_url, content=image_bytes)

                if response.status_code == 503:
                    response_json = response.json()
                    estimated_time = response_json.get("estimated_time", initial_delay)
                    self.log.print(
                        f"{self.log.YELLOW}Model sedang dimuat, menunggu {estimated_time:.1f} detik... (Percobaan {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(estimated_time)
                    continue

                response.raise_for_status()
                return response.content

            except httpx.HTTPStatusError as e:
                error_details = str(e.response.text)
                try:
                    error_details = e.response.json().get("error", str(e.response.text))
                except Exception:
                    pass
                raise Exception(f"Gagal mengonversi gambar: {e.response.status_code} - {error_details}")
            except Exception as e:
                raise Exception(f"Terjadi kesalahan saat menghubungi Hugging Face API: {e}")

        raise Exception(f"Model tidak siap setelah {max_retries} percobaan. Coba lagi nanti.")
