import datetime
import logging
import os
import sys
import zoneinfo
from typing import Optional

from .colorize import AnsiColors


class LoggerHandler(AnsiColors):
    def __init__(self, **options):
        super().__init__()
        self.tz = zoneinfo.ZoneInfo(options.get("tz", "Asia/Jakarta"))
        self.datefmt = options.get("datefmt", "%Y-%m-%d %H:%M:%S %Z")
        self.style = options.get("style", "minimal")
        self.show_emoji = options.get("show_emoji", True)
        
        self.colors = {
            "INFO": self.GREEN,
            "DEBUG": self.BLUE,
            "WARNING": self.YELLOW,
            "ERROR": self.RED,
            "CRITICAL": self.MAGENTA,
            "SUCCESS": self.LIGHT_GREEN,
            "TIME": self.CYAN,
            "MODULE": self.LIGHT_CYAN,
            "FUNC": self.PURPLE,
            "LINE": self.ORANGE,
            "PIPE": self.GRAY,
            "BOX": self.GRAY,
            "RESET": self.RESET,
        }
        
        self.icons = {
            "INFO": "ℹ️ ",
            "DEBUG": "🔍 ",
            "WARNING": "⚠️ ",
            "ERROR": "❌ ",
            "CRITICAL": "💥 ",
            "SUCCESS": "✅ ",
        }
        
        self.box = {
            "tl": "╭",
            "tr": "╮",
            "bl": "╰",
            "br": "╯",
            "h": "─",
            "v": "│",
            "sep": "├─",
        }

    def formatTime(self) -> str:
        utc_time = datetime.datetime.now(datetime.timezone.utc)
        local_time = utc_time.astimezone(self.tz)
        return local_time.strftime(self.datefmt)

    def _get_terminal_width(self) -> int:
        try:
            return os.get_terminal_size().columns
        except OSError:
            return 120

    def _format_modern(self, record: dict) -> str:
        level = record["levelname"]
        level_color = self.colors.get(level, self.RESET)
        box_color = self.colors["BOX"]
        time_color = self.colors["TIME"]
        module_color = self.colors["MODULE"]
        func_color = self.colors["FUNC"]
        line_color = self.colors["LINE"]
        
        icon = self.icons.get(level, "•") if self.show_emoji else "●"
        
        timestamp = self.formatTime()
        header = f"{box_color}{self.box['tl']}{self.box['h']*2} {time_color}{timestamp}{box_color} {self.box['h']*2}"
        
        level_line = (
            f"{box_color}{self.box['v']} "
            f"{level_color}{icon} {level:<8}{self.RESET} "
            f"{box_color}{self.box['v']} "
            f"{module_color}{record.get('module', '<unknown>')}{self.RESET}"
            f"{box_color}:{func_color}{record.get('funcName', '<unknown>')}{self.RESET}"
            f"{box_color}:{line_color}{record.get('lineno', 0)}{self.RESET}"
        )
        
        message_line = (
            f"{box_color}{self.box['sep']}{self.box['h']}▶ "
            f"{level_color}{record['message']}{self.RESET}"
        )
        
        return f"{header}\n{level_line}\n{message_line}"

    def _format_minimal(self, record: dict) -> str:
        level = record["levelname"]
        level_color = self.colors.get(level, self.RESET)
        icon = self.icons.get(level, "•") if self.show_emoji else "●"
        
        return (
            f"{self.colors['TIME']}{self.formatTime()}{self.RESET} "
            f"{level_color}{icon} {level:<8}{self.RESET} "
            f"{self.colors['MODULE']}{record.get('module', '?')}"
            f"{self.colors['PIPE']}:{self.colors['FUNC']}{record.get('funcName', '?')}"
            f"{self.colors['PIPE']}:{self.colors['LINE']}{record.get('lineno', 0)}{self.RESET} "
            f"{self.colors['PIPE']}│{self.RESET} "
            f"{level_color}{record['message']}{self.RESET}"
        )

    def _format_classic(self, record: dict) -> str:
        level = record["levelname"]
        level_color = self.colors.get(level, self.RESET)
        pipe_color = self.colors["PIPE"]
        
        return (
            f"{self.colors['TIME']}[ {self.formatTime()} ] "
            f"{pipe_color}│ {level_color}{level:<8} "
            f"{pipe_color}│ {self.colors['MODULE']}{record.get('module', '<unknown>')}"
            f":{record.get('funcName', '<unknown>')}"
            f":{record.get('lineno', 0)} "
            f"{pipe_color}│ {level_color}{record['message']}{self.RESET}"
        )

    def format(self, record: dict) -> str:
        if self.style == "modern":
            return self._format_modern(record)
        elif self.style == "minimal":
            return self._format_minimal(record)
        else:
            return self._format_classic(record)

    def print(self, message: str, isPrint: bool = True) -> Optional[str]:
        width = min(self._get_terminal_width(), 80)
        text = (
            f"{self.CYAN}{self.box['tl']}{self.box['h']} "
            f"{self.WHITE}{self.formatTime()} "
            f"{self.CYAN}{self.box['h']*width}{self.box['tr']}\n"
            f"{self.CYAN}{self.box['sep']} {self.WHITE}{message}{self.RESET}\n"
            f"{self.CYAN}{self.box['bl']}{self.box['h']*width}{self.box['br']"
        )
        if isPrint:
            print(f"\033[2K{text}")
        else:
            return text

    def banner(self, title: str, subtitle: str = ""):
        width = min(self._get_terminal_width(), 80)
        box_color = self.colors["BOX"]
        
        print(f"\n{box_color}{self.box['tl']}{self.box['h'] * (width - 2)}{self.box['tr']}")
        print(f"{box_color}{self.box['v']}{self.CYAN}{title.center(width - 2)}{box_color}{self.box['v']}")
        if subtitle:
            print(f"{box_color}{self.box['v']}{self.WHITE}{subtitle.center(width - 2)}{box_color}{self.box['v']}")
        print(f"{box_color}{self.box['bl']}{self.box['h'] * (width - 2)}{self.box['br']}{self.RESET}\n")

    def separator(self, char: str = "─", color: str = None):
        width = min(self._get_terminal_width(), 80)
        color = color or self.colors["BOX"]
        print(f"{color}{char * width}{self.RESET}")

    def log(self, level: str, message: str):
        frame = sys._getframe(2)
        filename = os.path.basename(frame.f_globals.get("__file__", "<unknown>"))
        
        record = {
            "levelname": level,
            "module": filename.replace(".py", ""),
            "funcName": frame.f_code.co_name,
            "lineno": frame.f_lineno,
            "message": message,
        }
        
        formatted_message = self.format(record)
        print(f"\033[2K{formatted_message}")

    def debug(self, message: str):
        self.log("DEBUG", message)

    def info(self, message: str):
        self.log("INFO", message)

    def success(self, message: str):
        self.log("SUCCESS", message)

    def warning(self, message: str):
        self.log("WARNING", message)

    def error(self, message: str):
        self.log("ERROR", message)

    def critical(self, message: str):
        self.log("CRITICAL", message)


class CustomLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.formatter_util = LoggerHandler()

    def emit(self, record: logging.LogRecord):
        custom_record = {
            "levelname": record.levelname,
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
            "message": record.getMessage(),
        }
        try:
            msg = self.formatter_util.format(custom_record)
            print(f"\033[2K{msg}")
        except Exception:
            self.handleError(record)
