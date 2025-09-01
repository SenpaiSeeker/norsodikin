import asyncio
from functools import wraps
from typing import Callable, List, Tuple

try:
    import aiocron
except ImportError:
    aiocron = None

class Scheduler:
    def __init__(self):
        self.jobs: List[Tuple[str, Callable]] = []
        self._is_started = False

    def add_job(self, spec: str, func: Callable):
        self.jobs.append((spec, func))

    def cron(self, spec: str):
        def decorator(func):
            self.add_job(spec, func)
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def start(self):
        if self._is_started:
            return
        
        loop = asyncio.get_event_loop()
        for spec, func in self.jobs:
            aiocron.crontab(spec, func=func, loop=loop)
        
        self._is_started = True
