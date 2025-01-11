class Gradient:
    def __init__(self):
        self.figlet = __import__("pyfiglet").Figlet(font="slant")
        self.random = __import__("random")
        self.asyncio = __import__("asyncio")
        self.start_color = self.random_color()
        self.end_color = self.random_color()

    def random_color(self):
        return (
            self.random.randint(128, 255),
            self.random.randint(128, 255),
            self.random.randint(128, 255),
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

    async def countdown(self, seconds, text="Tunggu sebentar {time} untuk melanjutkan", bar_length=30):
        print()
        for remaining in range(seconds, -1, -1):
            if remaining >= 3600:
                time_display = f"{remaining // 3600:02}:{(remaining % 3600) // 60:02}:{remaining % 60:02}"
            elif remaining >= 60:
                time_display = f"{remaining // 60:02}:{remaining % 60:02}"
            else:
                time_display = f"{remaining:02}"

            color = [self.rgb_to_ansi(*self.random_color()) for _ in range(3)]
            reset_color = "\033[0m"

            progress_percentage = f"{color[1]}{int(((seconds - remaining) / seconds) * 100) if seconds > 0 else 100}%"
            progress = int(((seconds - remaining) / seconds) * bar_length) if seconds > 0 else bar_length
            bar = f"{color[0]}[{'■' * progress}{'□' * (bar_length - progress)}]"

            print(f"\033[2K\r{bar} {progress_percentage} {color[2]}{text.format(time=time_display)}{reset_color}", end="", flush=True)
            await self.asyncio.sleep(1)
        print()
