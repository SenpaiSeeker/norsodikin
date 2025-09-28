from io import BytesIO

import httpx


class TelegraphUploader:
    def __init__(self, timeout: int = 30):
        self.upload_url = "https://telegra.ph/upload"
        self.base_url = "https://telegra.ph"
        self.timeout = timeout

    async def upload(self, file_bytes: bytes, file_name: str = "file.png") -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                file_to_upload = (file_name, BytesIO(file_bytes), "image/png")
                files = {"file": file_to_upload}

                response = await client.post(self.upload_url, files=files)
                response.raise_for_status()

                result = response.json()
                if isinstance(result, list) and result and "src" in result[0]:
                    return self.base_url + result[0]["src"]
                else:
                    raise Exception("Format respons API tidak valid.")

            except httpx.RequestError as e:
                raise Exception(f"Gagal terhubung ke API Telegraph: {e}")
            except (httpx.HTTPStatusError, KeyError, IndexError, Exception) as e:
                raise Exception(f"Gagal mengunggah ke Telegraph: {e}")
