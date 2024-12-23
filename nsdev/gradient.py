import random

from pyfiglet import Figlet


class Gradient:
    def __init__(self):
        self.start_color = self.random_color()
        self.end_color = self.random_color()
        self.figlet = Figlet(font="slant")

    def random_color(self):
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

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
