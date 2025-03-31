class LoggerHandler:
    def __init__(self, **options):
        """
        Inisialisasi logger dengan parameter opsional.

        :param options:
            - tz: Zona waktu untuk waktu lokal (default: 'Asia/Jakarta')
            - fmt: Format log (default: '{asctime} {levelname} {module}:{funcName}:{lineno} {message}')
            - datefmt: Format tanggal dan waktu (default: '%Y-%m-%d %H:%M:%S')
        """
        self.datetime = __import__("datetime")
        self.zoneinfo = __import__("zoneinfo")
        self.sys = __import__("sys")
        self.os = __import__("os")

        self.tz = self.zoneinfo.ZoneInfo(options.get("tz", "Asia/Jakarta"))
        self.fmt = options.get("fmt", "{asctime} {levelname} {module}:{funcName}:{lineno} {message}")
        self.datefmt = options.get("datefmt", "%Y-%m-%d %H:%M:%S %Z")
        self.colors = {
            "GREEN": "\033[1;38;5;46m",
            "BLUE": "\033[1;38;5;21m",
            "YELLOW": "\033[1;38;5;226m",
            "RED": "\033[1;38;5;196m",
            "MAGENTA": "\033[1;38;5;201m",
            "WHITE": "\033[1;38;5;231m",
            "CYAN": "\033[1;38;5;51m",
            "PURPLE": "\033[1;38;5;93m",
            "RESET": "\033[0m",
        }

    def get_colors(self):
        return {
            "INFO": self.colors["GREEN"],  # Green maksimal (0,5,0)
            "DEBUG": self.colors["BLUE"],  # Blue murni (0,0,5)
            "WARNING": self.colors["YELLOW"],  # Yellow murni (5,5,0)
            "ERROR": self.colors["RED"],  # Red murni (5,0,0)
            "CRITICAL": self.colors["MAGENTA"],  # Magenta murni (5,0,5)
            "TIME": self.colors["WHITE"],  # White penuh (5,5,5)
            "MODULE": self.colors["CYAN"],  # Cyan murni (0,5,5)
            "PIPE": self.colors["PURPLE"],  # Ungu terang untuk simbol '|'
        }

    def formatTime(self, record):
        utc_time = self.datetime.datetime.utcfromtimestamp(record["created"])
        local_time = utc_time.astimezone(self.tz)
        return local_time.strftime(self.datefmt)

    def format(self, record, isNoModuleLog=False):
        level_color = self.get_colors().get(record["levelname"], self.colors["RESET"])
        pipe_color = self.get_colors()["PIPE"]

        record["levelname"] = f"{pipe_color}|{self.colors['RESET']} {level_color}{record['levelname']:<8}"
        record["message"] = f"{pipe_color}|{self.colors['RESET']} {level_color}{record['message']}{self.colors['RESET']}"

        formatted_time = self.formatTime(record)

        if isNoModuleLog:
            fmt = "{asctime} {levelname} {message}"
            return fmt.format(
                asctime=f"{self.get_colors()['TIME']}[{formatted_time}]",
                levelname=record["levelname"],
                message=record["message"],
            )
        else:
            return self.fmt.format(
                asctime=f"{self.get_colors()['TIME']}[{formatted_time}]",
                levelname=record["levelname"],
                module=f"{pipe_color}|{self.colors['RESET']} {self.get_colors()['MODULE']}{self.os.path.basename(record.get('module', '<unknown>'))}",
                funcName=record.get("funcName", "<unknown>"),
                lineno=record.get("lineno", 0),
                message=record["message"],
            )

    def log(self, level, message, isNoModuleLog=False):
        frame = self.sys._getframe(2)
        filename = self.os.path.basename(frame.f_globals.get("__file__", "<unknown>"))
        record = {
            "created": self.datetime.datetime.now().timestamp(),
            "levelname": level,
            "module": filename if not isNoModuleLog else "",
            "funcName": frame.f_code.co_name if not isNoModuleLog else "",
            "lineno": frame.f_lineno if not isNoModuleLog else "",
            "message": message,
        }
        formatted_message = self.format(record, isNoModuleLog=isNoModuleLog)
        print(formatted_message)

    def debug(self, message, isNoModuleLog=False):
        self.log("DEBUG", message, isNoModuleLog=isNoModuleLog)

    def info(self, message, isNoModuleLog=False):
        self.log("INFO", message, isNoModuleLog=isNoModuleLog)

    def warning(self, message, isNoModuleLog=False):
        self.log("WARNING", message, isNoModuleLog=isNoModuleLog)

    def error(self, message, isNoModuleLog=False):
        self.log("ERROR", message, isNoModuleLog=isNoModuleLog)

    def critical(self, message, isNoModuleLog=False):
        self.log("CRITICAL", message, isNoModuleLog=isNoModuleLog)


log = LoggerHandler()
log.info(f"{log.colors['CYAN']}Ini {log.colors['BLUE']}pesan {log.colors['WHITE']}log", True)
log.debug("Ini pesan log")
log.error("Ini pesan log")
log.warning("Ini pesan log")
log.critical("Ini pesan log")
