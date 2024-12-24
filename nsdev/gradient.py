class Gradient:
    def __init__(self):
        self.start_color = self.random_color()
        self.end_color = self.random_color()
        self.figlet = __import__("pyfiglet").Figlet(font="slant")
        self.random = __import__("random")
        self.time = __import__("time")

    def random_color(self):
        return (
            self.random.randint(0, 255),
            self.random.randint(0, 255),
            self.random.randint(0, 255),
        )

    def rgb_to_ansi(self, r, g, b):
        return f"\033[38;2;{r};{g};{b}m"

    def interpolate_color(self, factor):
        return (
            int(self.start_color[0] + (self.end_color[0] - self.start_color[0]) * factor),
            int(self.start_color[1] + (self.end_color[1] - self.start_color[1]) * factor),
            int(self.start_color[2] + (self.end_color[2] - self.start_color[2]) * factor),
        )

    def render_text(self, text):
        text = self.figlet.renderText(text)
        for i, char in enumerate(text):
            factor = i / max(len(text) - 1, 1)
            r, g, b = self.interpolate_color(factor)
            print(self.rgb_to_ansi(r, g, b) + char, end="")
        print("\033[0m")

    def countdown(self, seconds):
        for remaining in range(seconds, -1, -1):
            hours, remainder = divmod(remaining, 3600)
            minutes, secs = divmod(remainder, 60)
            r, g, b = self.random_color()
            color = self.rgb_to_ansi(r, g, b)
            print(f"{color}===== Tunggu sebentar {hours:02}:{minutes:02}:{secs:02} untuk melanjutkan =====\033[0m", end="\r", flush=True)
            self.time.sleep(1)
        print()
