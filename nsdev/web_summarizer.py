class WebSummarizer:
    def __init__(self, gemini_instance):
        if not gemini_instance:
            raise ValueError("WebSummarizer memerlukan instance dari ChatbotGemini.")
        self.gemini = gemini_instance
        self.httpx = __import__("httpx")
        self.bs4 = __import__("bs4")
        self.uuid = __import__("uuid")

    async def _scrape_text(self, url: str) -> str:
        async with self.httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                soup = self.bs4.BeautifulSoup(response.text, "lxml")
                for script_or_style in soup(["script", "style"]):
                    script_or_style.decompose()
                paragraphs = soup.find_all("p")
                text = " ".join(p.get_text(strip=True) for p in paragraphs)
                if not text:
                    text = soup.body.get_text(separator=" ", strip=True)
                return text
            except Exception as e:
                raise Exception(f"Gagal mengambil konten dari URL: {e}")

    async def summarize(self, url: str, bot_name: str = "PeringkasAhli", max_length: int = 8000) -> str:
        try:
            scraped_text = await self._scrape_text(url)
            if not scraped_text.strip():
                return "Tidak dapat menemukan konten teks yang bisa dirangkum dari URL ini."
            truncated_text = scraped_text[:max_length]
            prompt = (
                "Anda adalah seorang ahli dalam meringkas artikel. "
                "Tugas Anda adalah membaca teks berikut yang diambil dari sebuah halaman web dan membuat rangkuman yang jelas, padat, dan informatif dalam bahasa Indonesia. "
                "Fokus pada poin-poin utama dan abaikan detail yang tidak penting.\n\n"
                "Berikut adalah teksnya:\n\n---\n\n"
                f"{truncated_text}"
            )
            summary_session_id = f"summary-{self.uuid.uuid4()}"
            summary = self.gemini.send_chat_message(prompt, user_id=summary_session_id, bot_name=bot_name)
            return summary
        except Exception as e:
            return f"Terjadi kesalahan saat merangkum: {e}"
