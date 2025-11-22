import platform
import time
from datetime import timedelta
from types import SimpleNamespace

import psutil


class ServerMonitor:
    def __init__(self):
        self.boot_time = psutil.boot_time()

    def _create_progress_bar(self, percentage: float, length: int = 10) -> str:
        filled_length = int(length * percentage // 100)
        bar = "█" * filled_length + "░" * (length - filled_length)
        return bar

    def _get_uptime(self) -> str:
        uptime_seconds = time.time() - self.boot_time
        return str(timedelta(seconds=int(uptime_seconds)))

    def _format_bytes(self, size: float) -> str:
        power = 2**10
        n = 0
        power_labels = {0: "", 1: "K", 2: "M", 3: "G", 4: "T"}
        while size > power:
            size /= power
            n += 1
        return f"{size:.2f} {power_labels[n]}B"

    def get_detailed_stats(self) -> SimpleNamespace:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_bar = self._create_progress_bar(cpu_percent)
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count()

        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        ram_bar = self._create_progress_bar(ram_percent)
        ram_used = self._format_bytes(ram.used)
        ram_total = self._format_bytes(ram.total)

        disk = psutil.disk_usage("/")
        disk_percent = disk.percent
        disk_bar = self._create_progress_bar(disk_percent)
        disk_used = self._format_bytes(disk.used)
        disk_total = self._format_bytes(disk.total)

        net = psutil.net_io_counters()
        sent = self._format_bytes(net.bytes_sent)
        recv = self._format_bytes(net.bytes_recv)

        system_info = {
            "os": f"{platform.system()} {platform.release()}",
            "python": platform.python_version(),
            "uptime": self._get_uptime(),
            "cpu": {
                "percent": cpu_percent,
                "bar": cpu_bar,
                "freq": f"{cpu_freq.current:.0f}Mhz" if cpu_freq else "N/A",
                "cores": cpu_count,
            },
            "ram": {"percent": ram_percent, "bar": ram_bar, "used": ram_used, "total": ram_total},
            "disk": {"percent": disk_percent, "bar": disk_bar, "used": disk_used, "total": disk_total},
            "network": {"sent": sent, "recv": recv},
        }

        return SimpleNamespace(**system_info)

    def get_stats(self):
        return self.get_detailed_stats()
