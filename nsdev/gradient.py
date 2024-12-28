class Gradient:
    def __init__(self):
        self.figlet = __import__("pyfiglet").Figlet(font="slant")
        self.random = __import__("random")
        self.time = __import__("time")
        self.start_color = self.random_color()
        self.end_color = self.random_color()

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
        rendered_text = self.figlet.renderText(text)
        for i, char in enumerate(rendered_text):
            factor = i / max(len(rendered_text) - 1, 1)
            r, g, b = self.interpolate_color(factor)
            print(self.rgb_to_ansi(r, g, b) + char, end="")
        print("\033[0m")

    def countdown(self, seconds, text="Tungu sebentar {time} untuk melanjutkan"):
        bar_length = 30
        print()
        for remaining in range(seconds, -1, -1):
            hours, remainder = divmod(remaining, 3600)
            minutes, secs = divmod(remainder, 60)
            time_display = f"{hours:02}:{minutes:02}:{secs:02}"

            r, g, b = self.random_color()
            color = self.rgb_to_ansi(r, g, b)

            progress = int(((seconds - remaining) / seconds) * bar_length) if seconds > 0 else bar_length
            bar = "=" * progress + "-" * (bar_length - progress)

            print(f"\033[2K\r{color}[{bar}] {text.format(time=time_display)}\033[0m", end="", flush=True)
            self.time.sleep(1)
        print()
