async def generate(self, prompt: str, max_wait_seconds: int = 300):
    if not prompt:
        raise ValueError("Prompt tidak boleh kosong.")

    start_time = time.time()
    self.__log(f"{self.log.GREEN}Memulai pembuatan gambar untuk prompt: '{prompt}'")
    encoded_prompt = urllib.parse.quote(prompt)

    url = f"/images/create?q={encoded_prompt}&rt=4&FORM=GENCRE&aid=DALL-E3"

    try:
        response = await self.client.post(url)
    except httpx.RequestError as e:
        raise Exception(f"Gagal mengirim permintaan pembuatan gambar: {e}")

    if response.status_code != 302:
        self.__log(f"{self.log.RED}Status code tidak valid: {response.status_code}. Mungkin cookie tidak valid.")
        self.__log(f"{self.log.RED}Response: {response.text[:250]}...")
        raise Exception("Permintaan gagal. Pastikan cookie _U valid dan tidak kadaluarsa.")

    redirect_url = response.headers.get("Location")
    if not redirect_url or "id=" not in redirect_url:
        raise Exception("Gagal mendapatkan ID permintaan dari redirect. Prompt mungkin diblokir.")

    request_id = re.search(r"id=([^&]+)", redirect_url).group(1)
    self.__log(f"{self.log.GREEN}Permintaan berhasil dikirim. ID: {request_id}")
    polling_url = f"/images/create/async/results/{request_id}?q={encoded_prompt}"
    self.__log(f"{self.log.GREEN}Menunggu hasil gambar...")

    wait_start_time = time.time()
    while True:
        if time.time() - wait_start_time > max_wait_seconds:
            raise Exception(f"Waktu tunggu habis ({max_wait_seconds} detik).")

        try:
            poll_response = await self.client.get(polling_url)
        except httpx.RequestError as e:
            self.__log(f"{self.log.YELLOW}Gagal polling, mencoba lagi... Error: {e}")
            await asyncio.sleep(2)
            continue

        if poll_response.status_code != 200:
            self.__log(f"{self.log.YELLOW}Status polling tidak 200, mencoba lagi...")
            await asyncio.sleep(2)
            continue

        if "errorMessage" in poll_response.text:
            error_message = re.search(r'<div id="gil_err_msg">([^<]+)</div>', poll_response.text)
            raise Exception(f"Bing error: {error_message.group(1)}")

        image_urls = re.findall(r'src="([^"]+)"', poll_response.text)
        processed_urls = list(set([url.split("?w=")[0] for url in image_urls if "bing.net" in url and not "OIG" in url]))

        if processed_urls:
            self.__log(
                f"{self.log.GREEN}Ditemukan {len(processed_urls)} gambar final. Total waktu: {round(time.time() - start_time, 2)}s."
            )
            return processed_urls

        await asyncio.sleep(3)
