class HuggingFaceGenerator:
    def __init__(
        self,
        api_key: str,
        model_id: str = "stabilityai/stable-diffusion-xl-base-1.0",
        logging_enabled: bool = True,
    ):
        self.asyncio = __import__("asyncio")
        self.time = __import__("time")
        self.httpx = __import__("httpx")

        self.api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.client = self.httpx.AsyncClient(headers=self.headers, timeout=300)
        self.logging_enabled = logging_enabled

        self.log = __import__("nsdev").logger.LoggerHandler()

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    async def _generate_single_image(self, prompt: str, retry_delay: int = 10, max_retries: int = 3):
        payload = {"inputs": prompt}
        for attempt in range(max_retries):
            try:
                response = await self.client.post(self.api_url, json=payload)

                if response.status_code == 503:
                    response_json = response.json()
                    estimated_time = response_json.get("estimated_time", retry_delay)
                    self.__log(
                        f"{self.log.YELLOW}Model sedang loading, menunggu {estimated_time:.1f} detik... (Percobaan {attempt + 1}/{max_retries})"
                    )
                    await self.asyncio.sleep(estimated_time)
                    continue

                response.raise_for_status()
                return response.content

            except self.httpx.HTTPStatusError as e:
                error_details = e.response.json().get("error", str(e.response.text))
                raise Exception(f"Gagal menghasilkan gambar: {e.response.status_code} - {error_details}")
            except Exception as e:
                raise Exception(f"Terjadi kesalahan saat menghubungi Hugging Face API: {e}")

        raise Exception(f"Model tidak siap setelah {max_retries} percobaan. Coba lagi nanti.")

    async def generate(self, prompt: str, num_images: int = 1):
        start_time = self.time.time()
        self.__log(f"{self.log.GREEN}Memulai pembuatan {num_images} gambar dari Hugging Face untuk prompt: '{prompt}'")

        tasks = [self._generate_single_image(prompt) for _ in range(num_images)]
        results = await self.asyncio.gather(*tasks, return_exceptions=True)

        successful_images = []
        for res in results:
            if isinstance(res, bytes):
                successful_images.append(res)
            else:
                self.__log(f"{self.log.RED}Satu tugas pembuatan gambar gagal: {res}")

        if not successful_images:
            raise Exception("Semua tugas pembuatan gambar gagal.")

        self.__log(
            f"{self.log.GREEN}Berhasil membuat {len(successful_images)} gambar dalam {self.time.time() - start_time:.2f} detik."
        )
        return successful_images
