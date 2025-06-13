class ImageGenerator:
    def __init__(self, auth_cookie_u: str, auth_cookie_srchhpgusr: str, logging_enabled: bool = True):
        self.httpx = __import__("httpx")
        self.re = __import__("re")
        self.time = __import__("time")
        self.urllib = __import__("urllib")
        self.client = self.httpx.AsyncClient(
            cookies={"_U": auth_cookie_u, "SRCHHPGUSR": auth_cookie_srchhpgusr},
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.bing.com/" 
            }
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
                results_url = f"https://www.bing.com/images/create/async/results/{result_id}?q={cleaned_translated_prompt}"
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
                    new_images = list(set(["https://tse" + link.split("?w=")[0] for link in self.re.findall(r'src="https://tse([^"]+)"', response.text)]))
                except Exception as e:
                    self.__log(f"{self.log.RED}Gagal mengekstrak gambar: {e}")
                    new_images = []

                if new_images:
                    break

                self.time.sleep(1)

            images.extend(new_images)
            self.__log(f"{self.log.GREEN}Siklus {cycle} selesai dalam {round(self.time.time() - start_cycle_time, 2)} detik.")

        self.__log(f"{self.log.GREEN}Pembuatan gambar selesai dalam {round(self.time.time() - start_time, 2)} detik.")
        return images[:num_images]

/eval import requests
from bs4 import BeautifulSoup

# URL target (misalnya halaman pencarian gambar Bing)
url = "https://www.bing.com/images/create" 

# Cookies yang diperlukan (Anda harus mendapatkan cookies ini dari sesi browser Anda)
cookies = {
    # Ganti dengan cookies yang valid dari sesi Anda
    "_U": "1ewaLJjPia7P4DG_NsMPYcVhmTF-njPL4h3KVmopIjVK9j-S7kUG2xhxnmtHv5x-n-pPQvkRliCrNunKt2o078mmMTXMzGslwpg5We-9RudoT0yyr4TLyNxuHK2NhkDwGMpqNfTj89anPclN9RjvsVHyNQFcrbO03Vm0Gk3dj4lRbnuu1CjGB6i6NzI4u3esX5JJGJKvcfmgiy1nPYbmxuw",
    "SRCHHPGUSR": "SRCHLANG=id&IG=FA8775C26BDB4C37AAB0F87570B9B751&DM=1&BRW=M&BRH=S&CW=1325&CH=661&SCW=1326&SCH=661&DPR=1.5&UTC=420&HV=1749790146&HVE=CfDJ8Inh5QCoSQBNls38F2rbEpRLdgYGUEzSBinYFQAdQfDlrJUPnL45ofQK8wvKMkGC_f6YsLQ9rk9QqdHs_aD7NwjafNXAhGoVWkMZ8XLkYidSvPadzGC612c2Wm_UeWWIxmjxkQOZ94c6yV7NoUjy-epQyfY9O3OtnUpQl3dokMjVmWqGFk3jsuh-OYgiuyc2jg&PRVCW=1325&PRVCH=661&WTS=63885386946&PREFCOL=1"
}

# Headers untuk mensimulasikan permintaan dari browser


# Data payload untuk deskripsi gambar (contoh: "seorang astronot bermain gitar di bulan")
payload = {
    "q": """Ilustrasi anime chibi seorang cowok imut dengan ekspresi ceria yang menular. Ia mengenakan hoodie putih bersih dengan tulisan "NOR SODIKIN" dalam font small caps futuristik, efek glow 3D timbul yang memancarkan cahaya lembut. Latar belakangnya adalah langit malam bertabur bintang berkilauan, dengan sentuhan magis tema pemrograman Python: kode-kode Python bercahaya melayang di antara bintang, menciptakan suasana digital-astral yang memukau. Gaya artistik: dreamy, ethereal, dengan palet warna neon lembut dan efek bokeh yang indah.""",
    "FORM": "CREATED"
}

# Kirim permintaan POST ke server Bing
response = requests.post(url, headers=headers, cookies=cookies, data=payload)

# Periksa apakah permintaan berhasil
if response.status_code == 200:
    print("Permintaan berhasil!")
    
    # Parsing HTML menggunakan BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Cari elemen yang mengandung gambar hasil
    image_elements = soup.find_all("img")  # Sesuaikan dengan struktur HTML Bing
    
    for img in image_elements:
        src = img.get("src")
        if src and src.startswith("http"):  # Pastikan URL gambar valid
            await message.reply_photo(url)
else:
    print(f"Permintaan gagal dengan status code: {response.status_code}")
