class TextToSpeech:
    def __init__(self):
        self.gTTS = __import__("gtts").gTTS
        self.BytesIO = __import__("io").BytesIO
        self.asyncio = __import__("asyncio")

    def _sync_generate(self, text: str, lang: str):
        try:
            tts = self.gTTS(text=text, lang=lang, slow=False)
            fp = self.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.getvalue()
        except Exception as e:
            return e

    async def generate(self, text: str, lang: str = "id") -> bytes:
        loop = self.asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._sync_generate, text, lang)
        if isinstance(result, Exception):
            raise result
        return result
