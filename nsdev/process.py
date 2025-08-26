import asyncio
import psutil
from types import SimpleNamespace

class ProcessManager:
    def _sync_get_processes(self, limit: int, sort_by: str) -> list:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                pinfo['memory_percent'] = round(pinfo['memory_percent'], 2)
                pinfo['cpu_percent'] = round(pinfo['cpu_percent'], 2)
                processes.append(SimpleNamespace(**pinfo))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        valid_sort_keys = ['pid', 'name', 'username', 'cpu_percent', 'memory_percent']
        sort_key = sort_by if sort_by in valid_sort_keys else 'cpu_percent'

        processes.sort(key=lambda p: getattr(p, sort_key, 0), reverse=True)
        return processes[:limit]

    async def list(self, limit: int = 10, sort_by: str = 'cpu_percent') -> list:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_get_processes, limit, sort_by)

    def _sync_kill_process(self, pid: int) -> bool:
        try:
            proc = psutil.Process(pid)
            proc.kill()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    async def kill(self, pid: int) -> bool:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_kill_process, pid)
