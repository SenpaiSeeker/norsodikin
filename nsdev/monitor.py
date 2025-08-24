class ServerMonitor:
    def __init__(self):
        self.psutil = __import__("psutil")
        self.SimpleNamespace = __import__("types").SimpleNamespace

    def get_stats(self):
        cpu_percent = self.psutil.cpu_percent(interval=1)
        ram = self.psutil.virtual_memory()
        ram_total_gb = ram.total / (1024**3)
        ram_used_gb = ram.used / (1024**3)
        ram_percent = ram.percent
        disk = self.psutil.disk_usage("/")
        disk_total_gb = disk.total / (1024**3)
        disk_used_gb = disk.used / (1024**3)
        disk_percent = disk.percent
        return self.SimpleNamespace(
            cpu_percent=cpu_percent,
            ram_total_gb=ram_total_gb,
            ram_used_gb=ram_used_gb,
            ram_percent=ram_percent,
            disk_total_gb=disk_total_gb,
            disk_used_gb=disk_used_gb,
            disk_percent=disk_percent,
        )
