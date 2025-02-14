class LoggerHandler:
    def __init__(self, **options):
        """
        Inisialisasi logger dengan parameter opsional.

        :param options:
            - log_level: Level log (default: 'DEBUG')
            - tz: Zona waktu untuk waktu lokal (default: 'Asia/Jakarta')
            - fmt: Format log (default: '{asctime} {levelname} {module}:{funcName}:{lineno} {message}')
            - datefmt: Format tanggal dan waktu (default: '%Y-%m-%d %H:%M:%S')
        """
        self.LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
        self.datetime = __import__("datetime")
        self.zoneinfo = __import__("zoneinfo")
        self.sys = __import__("sys")
        self.os = __import__("os")

        self.log_level = self.LEVELS.get(options.get("log_level", "DEBUG").upper(), 20)
        self.tz = self.zoneinfo.ZoneInfo(options.get("tz", "Asia/Jakarta"))
        self.fmt = options.get("fmt", "{asctime} {levelname} {module}:{funcName}:{lineno} {message}")
        self.datefmt = options.get("datefmt", "%Y-%m-%d %H:%M:%S")

    def formatTime(self, record):
        utc_time = self.datetime.datetime.utcfromtimestamp(record["created"])
        local_time = utc_time.astimezone(self.tz)
        return local_time.strftime(self.datefmt)

    def format(self, record):
        COLORS = {
    "INFO": "\033[1;38;5;46m",    # Green maksimal (0,5,0)
    "DEBUG": "\033[1;38;5;21m",    # Blue murni (0,0,5)
    "WARNING": "\033[1;38;5;226m", # Yellow murni (5,5,0)
    "ERROR": "\033[1;38;5;196m",   # Red murni (5,0,0)
    "CRITICAL": "\033[1;38;5;201m",# Magenta murni (5,0,5)
    "TIME": "\033[1;38;5;231m",    # White penuh (5,5,5)
    "MODULE": "\033[1;38;5;51m",   # Cyan murni (0,5,5)
    "RESET": "\033[0m",
}


        level_color = COLORS.get(record["levelname"], COLORS["RESET"])
        record["levelname"] = f"{level_color}| {record['levelname']:<8}"
        record["message"] = f"{level_color}| {record['message']}{COLORS['RESET']}"

        formatted_time = self.formatTime(record)
        return self.fmt.format(
            asctime=f"{COLORS['TIME']}[{formatted_time}]",
            levelname=record["levelname"],
            module=f"{COLORS['MODULE']}| {self.os.path.basename(record.get('module', '<unknown>'))}",
            funcName=record.get("funcName", "<unknown>"),
            lineno=record.get("lineno", 0),
            message=record["message"],
        )

    def log(self, level, message):
        if self.LEVELS.get(level, 0) >= self.log_level:
            frame = self.sys._getframe(2)
            filename = self.os.path.basename(frame.f_globals.get("__file__", "<unknown>"))
            record = {
                "created": self.datetime.datetime.now().timestamp(),
                "levelname": level,
                "module": filename,
                "funcName": frame.f_code.co_name,
                "lineno": frame.f_lineno,
                "message": message,
            }
            formatted_message = self.format(record)
            print(formatted_message)

    def debug(self, message):
        self.log("DEBUG", message)

    def info(self, message):
        self.log("INFO", message)

    def warning(self, message):
        self.log("WARNING", message)

    def error(self, message):
        self.log("ERROR", message)

    def critical(self, message):
        self.log("CRITICAL", message)
