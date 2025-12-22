import io
from shazamio import Shazam

class ShazamHelper:
    def __init__(self):
        self.shazam = Shazam()

    async def recognize(self, file_bytes: bytes):
        return await self.shazam.recognize(file_bytes)
