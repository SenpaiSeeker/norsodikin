import httpx


class ImageUpscaler:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key untuk DeepAI diperlukan.")
        self.api_key = api_key
        self.api_url = "https://api.deepai.org/api/torch-srgan"

    async def upscale(self, image_bytes: bytes) -> bytes:
        headers = {"api-key": self.api_key}
        files = {"image": image_bytes}

        async with httpx.AsyncClient(timeout=300) as client:
            try:
                response = await client.post(self.api_url, headers=headers, files=files)
                response.raise_for_status()
                result = response.json()

                if "output_url" not in result:
                    raise Exception(f"API error: {result.get('err', 'Unknown error')}")

                output_url = result["output_url"]
                image_response = await client.get(output_url)
                image_response.raise_for_status()

                return image_response.content

            except httpx.HTTPStatusError as e:
                raise Exception(f"Gagal menghubungi API DeepAI: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                raise Exception(f"Terjadi kesalahan saat upscale gambar: {e}")
