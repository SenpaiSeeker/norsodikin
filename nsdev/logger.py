class LoggerHandler(__import__("nsdev").AnsiColors):
    def __init__(self, **options):
        super().__init__()
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

    def get_colors(self):
        return {
            "INFO": self.GREEN,
            "DEBUG": self.BLUE,
            "WARNING": self.YELLOW,
            "ERROR": self.RED,
            "CRITICAL": self.MAGENTA,
            "TIME": self.WHITE,
            "MODULE": self.CYAN,
            "PIPE": self.PURPLE,
            "RESET": self.RESET,
        }

    def formatTime(self, record):
        utc_time = self.datetime.datetime.utcfromtimestamp(record["created"])
        local_time = utc_time.astimezone(self.tz)
        return local_time.strftime(self.datefmt)

    def format(self, record, isNoModuleLog=False):
        level_color = self.get_colors().get(record["levelname"], self.RESET)
        pipe_color = self.get_colors()["PIPE"]

        record["levelname"] = f"{pipe_color}| {level_color}{record['levelname']:<8}" if not isNoModuleLog else ""
        record["message"] = f"{pipe_color}| {level_color}{record['message']}{self.RESET}"
        
        formatted_time = self.formatTime(record)

        return (
            "{asctime} {message}".format(
                asctime=f"{self.get_colors()['TIME']}[{formatted_time}]",
                message=record["message"],
            )
            if isNoModuleLog
            else self.fmt.format(
                asctime=f"{self.get_colors()['TIME']}[{formatted_time}]",
                levelname=record["levelname"],
                module=f"{pipe_color}| {self.get_colors()['MODULE']}{self.os.path.basename(record.get('module', '<unknown>'))}",
                funcName=record.get("funcName", "<unknown>"),
                lineno=record.get("lineno", 0),
                message=record["message"],
            )
        )

    def log(self, level, message, isNoModuleLog=False):
        frame = self.sys._getframe(2)
        filename = self.os.path.basename(frame.f_globals.get("__file__", "<unknown>"))
        record = {
            "created": self.datetime.datetime.now().timestamp(),
            "levelname": level,
            "module": "" if isNoModuleLog else filename,
            "funcName": "" if isNoModuleLog else frame.f_code.co_name,
            "lineno": 0 if isNoModuleLog else frame.f_lineno,
            "message": message,
        }
        print(self.format(record, isNoModuleLog=isNoModuleLog))

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
