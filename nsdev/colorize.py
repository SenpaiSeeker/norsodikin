class AnsiColors:
    def __init__(self):
        self.RESET = "\033[0m"

        self.BLACK = "\033[1;38;5;16m"
        self.RED = "\033[1;38;5;196m"
        self.GREEN = "\033[1;38;5;46m"
        self.YELLOW = "\033[1;38;5;226m"
        self.BLUE = "\033[1;38;5;21m"
        self.MAGENTA = "\033[1;38;5;201m"
        self.CYAN = "\033[1;38;5;51m"
        self.WHITE = "\033[1;38;5;231m"
        self.ORANGE = "\033[1;38;5;208m"
        self.PINK = "\033[1;38;5;206m"
        self.GRAY = "\033[1;38;5;244m"
        self.BROWN = "\033[1;38;5;94m"
        self.AQUA = "\033[1;38;5;123m"
        self.PURPLE = "\033[1;38;5;93m"

        self.LIGHT_BLACK = "\033[1;38;5;235m"
        self.LIGHT_RED = "\033[1;38;5;203m"
        self.LIGHT_GREEN = "\033[1;38;5;120m"
        self.LIGHT_YELLOW = "\033[1;38;5;227m"
        self.LIGHT_BLUE = "\033[1;38;5;81m"
        self.LIGHT_MAGENTA = "\033[1;38;5;219m"
        self.LIGHT_CYAN = "\033[1;38;5;87m"
        self.LIGHT_WHITE = "\033[1;38;5;255m"
        self.LIGHT_ORANGE = "\033[1;38;5;214m"
        self.LIGHT_PINK = "\033[1;38;5;218m"
        self.LIGHT_GRAY = "\033[1;38;5;250m"
        self.LIGHT_BROWN = "\033[1;38;5;180m"
        self.LIGHT_AQUA = "\033[1;38;5;159m"
        self.LIGHT_PURPLE = "\033[1;38;5;183m"

    def print_all_colors(self):
        colors_dict = vars(self)
        for name, code in colors_dict.items():
            if name != "RESET":
                print(f"{code}{name.replace('_', ' ')}{self.RESET}")
