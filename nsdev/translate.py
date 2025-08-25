class Translator:
    def __init__(self):
        self.asyncio = __import__("asyncio")
        self.googletrans = __import__("googletrans")
        self._translator = self.googletrans.Translator()

    def _sync_translate(self, text: str, dest_lang: str):
        try:
            result = self._translator.translate(text, dest=dest_lang)
            return result
        except Exception as e:
            return e

    async def to(self, text: str, dest_lang: str = "en") -> str:
        loop = self.asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._sync_translate, text, dest_lang)
        if isinstance(result, Exception):
            raise result
        return result.text
