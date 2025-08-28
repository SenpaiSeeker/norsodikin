import asyncio
from io import BytesIO

from gtts import gTTS


class TextToSpeech:
    def _sync_generate(self, text: str, lang: str):
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.getvalue()
        except Exception as e:
            return e

    async def generate(self, text: str, lang: str = "id") -> bytes:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._sync_generate, text, lang)
        if isinstance(result, Exception):
            raise result
        return result
