import asyncio
import os
import shutil
import tempfile
from contextlib import asynccontextmanager

class FileManager:
    def _safe_rmtree(self, path):
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)

    @asynccontextmanager
    async def temp_dir(self):
        temp_dir_path = tempfile.mkdtemp()
        try:
            yield temp_dir_path
        finally:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._safe_rmtree, temp_dir_path)
