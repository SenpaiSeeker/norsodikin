class ImageGenerator:
    def __init__(
        self,
        auth_cookie_u: str,
        auth_cookie_srchhpgusr: str,
        logging_enabled: bool = True,
    ):
        self.httpx = __import__("httpx")
        self.re = __import__("re")
        self.time = __import__("time")
        self.urllib = __import__("urllib")
        self.user_agent = __import__("fake_useragent")
        self.client = self.httpx.AsyncClient(
            cookies={
                "_U": auth_cookie_u,
                "SRCHHPGUSR": auth_cookie_srchhpgusr,
            },
            headers={
                "User-Agent": self.user_agent.UserAgent().random,
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.bing.com/",
            },
        )
        self.logging_enabled = logging_enabled

        self.log = __import__("nsdev").logger.LoggerHandler()

    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    def __clean_text(self, text: str):
        cleaned_text = " ".join(text.split())
        return self.urllib.parse.quote(cleaned_text)

    async def generate(self, prompt: str, num_images: int, max_cycles: int = 4):
        images = []
        cycle = 0
        start_time = self.time.time()

        while len(images) < num_images and cycle < max_cycles:
            cycle += 1
            self.__log(f"{self.log.GREEN}Memulai siklus {cycle}...")

            translator = __import__("deep_translator").GoogleTranslator(source="auto", target="en")
            translated_prompt = translator.translate(prompt)
            cleaned_translated_prompt = self.__clean_text(translated_prompt)

            response = await self.client.post(
                url=f"https://www.bing.com/images/create?q={cleaned_translated_prompt}&rt=3&FORM=GENCRE",
                data={"q": cleaned_translated_prompt, "qs": "ds"},
                follow_redirects=False,
                timeout=200,
            )

            if response.status_code != 302:
                self.__log(f"{self.log.RED}Status code tidak valid: {response.status_code}")
                self.__log(f"{self.log.RED}Response: {response.text[:200]}...")
                raise Exception("Permintaan gagal! Pastikan URL benar dan ada redirect.")

            self.__log(f"{self.log.GREEN}Permintaan berhasil dikirim!")

            if "being reviewed" in response.text or "has been blocked" in response.text:
                raise Exception("Prompt sedang ditinjau atau diblokir!")
            if "image creator in more languages" in response.text:
                raise Exception("Bahasa yang digunakan tidak didukung oleh Bing!")

            try:
                result_id = response.headers["Location"].replace("&nfy=1", "").split("id=")[-1]
                results_url = (
                    f"https://www.bing.com/images/create/async/results/{result_id}?q={cleaned_translated_prompt}"
                )
            except KeyError:
                raise Exception("Gagal menemukan result_id dalam respons!")

            self.__log(f"{self.log.GREEN}Menunggu hasil gambar...")
            start_cycle_time = self.time.time()

            while True:
                response = await self.client.get(results_url)

                if self.time.time() - start_cycle_time > 200:
                    raise Exception("Waktu tunggu hasil habis!")

                if response.status_code != 200 or "errorMessage" in response.text:
                    self.time.sleep(1)
                    continue

                new_images = []
                try:
                    new_images = list(
                        set(
                            [
                                "https://tse" + link.split("?w=")[0]
                                for link in self.re.findall(r'src="https://tse([^"]+)"', response.text)
                            ]
                        )
                    )
                except Exception as e:
                    self.__log(f"{self.log.RED}Gagal mengekstrak gambar: {e}")
                    new_images = []

                if new_images:
                    break

                self.time.sleep(1)

            images.extend(new_images)
            self.__log(
                f"{self.log.GREEN}Siklus {cycle} selesai dalam {round(self.time.time() - start_cycle_time, 2)} detik."
            )

        self.__log(f"{self.log.GREEN}Pembuatan gambar selesai dalam {round(self.time.time() - start_time, 2)} detik.")
        return images[:num_images]
