class ImageGenerator:
    def __init__(self, auth_cookie_u: str, auth_cookie_srchhpgusr: str, logging_enabled: bool = True):
        self.httpx = __import__("httpx")
        self.re = __import__("re")
        self.time = __import__("time")
        self.urllib = __import__("urllib")
        self.client = self.httpx.AsyncClient(
            cookies={"_U": auth_cookie_u, "SRCHHPGUSR": auth_cookie_srchhpgusr},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "DNT": "1",
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

            try:
                translator = __import__("deep_translator").GoogleTranslator(source="auto", target="en")
                translated_prompt = translator.translate(prompt)
                cleaned_translated_prompt = self.__clean_text(translated_prompt)

                create_url = f"https://www.bing.com/images/create?{cleaned_translated_prompt}FORM=GENCRE"
                self.__log(f"{self.log.GREEN}Mengakses URL: {create_url}")

                response = await self.client.get(create_url)

                if response.status_code != 200:
                    self.__log(f"{self.log.RED}Status code tidak valid: {response.status_code}")
                    self.__log(f"{self.log.RED}Response: {response.text[:200]}...")
                    raise Exception("Gagal mengakses halaman create!")

                response = await self.client.post(
                    url=create_url,
                    data={"q": cleaned_translated_prompt, "qs": "ds"},
                    follow_redirects=False,
                    timeout=200,
                )

                if response.status_code != 302:
                    self.__log(f"{self.log.RED}Status code tidak valid: {response.status_code}")
                    self.__log(f"{self.log.RED}Response: {response.text[:200]}...")
                    raise Exception("Permintaan gagal! Pastikan URL benar dan ada redirect.")

                if "Location" not in response.headers:
                    raise Exception("Header Location tidak ditemukan dalam response!")

                location = response.headers["Location"]
                self.__log(f"{self.log.GREEN}Location header: {location}")

                if "id=" not in location:
                    raise Exception("ID tidak ditemukan dalam URL redirect!")

                result_id = location.replace("&nfy=1", "").split("id=")[-1]
                results_url = f"https://www.bing.com/images/create/async/results/{result_id}?q={cleaned_translated_prompt}"
                self.__log(f"{self.log.GREEN}URL hasil: {results_url}")

                self.__log(f"{self.log.GREEN}Menunggu hasil gambar...")
                start_cycle_time = self.time.time()

                while True:
                    try:
                        response = await self.client.get(results_url)

                        if self.time.time() - start_cycle_time > 200:
                            raise Exception("Waktu tunggu hasil habis!")

                        if response.status_code != 200:
                            self.__log(f"{self.log.YELLOW}Status code tidak 200: {response.status_code}")
                            self.time.sleep(1)
                            continue

                        if "errorMessage" in response.text:
                            self.__log(f"{self.log.YELLOW}Pesan error: {response.text[:200]}...")
                            self.time.sleep(1)
                            continue

                        new_images = []
                        try:
                            image_links = self.re.findall(r'src="https://tse([^"]+)"', response.text)
                            new_images = list(set(["https://tse" + link.split("?w=")[0] for link in image_links]))
                            self.__log(f"{self.log.GREEN}Ditemukan {len(new_images)} gambar baru")
                        except Exception as e:
                            self.__log(f"{self.log.RED}Gagal mengekstrak gambar: {e}")
                            new_images = []

                        if new_images:
                            break

                        self.time.sleep(1)
                    except Exception as e:
                        self.__log(f"{self.log.RED}Error saat mengambil hasil: {e}")
                        self.time.sleep(1)

                images.extend(new_images)
                self.__log(f"{self.log.GREEN}Siklus {cycle} selesai dalam {round(self.time.time() - start_cycle_time, 2)} detik.")

            except Exception as e:
                self.__log(f"{self.log.RED}Error pada siklus {cycle}: {e}")
                if cycle == max_cycles:
                    raise e
                continue

        self.__log(f"{self.log.GREEN}Pembuatan gambar selesai dalam {round(self.time.time() - start_time, 2)} detik.")
        return images[:num_images]
