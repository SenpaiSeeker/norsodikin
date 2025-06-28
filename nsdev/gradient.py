class Gradient:
    def __init__(self):
        self.figlet = __import__("pyfiglet").Figlet(font="slant")
        self.random = __import__("random")
        self.asyncio = __import__("asyncio")
        self.time = __import__("time")
        self.start_color = self.random_color()
        self.end_color = self.random_color()

    def random_color(self):
        return (
            self.random.randint(128, 255),
            self.random.randint(128, 255),
            self.random.randint(128, 255),
        )

    def rgb_to_ansi(self, r, g, b):
        r_scaled = int(round(r / 255 * 5))
        g_scaled = int(round(g / 255 * 5))
        b_scaled = int(round(b / 255 * 5))

        ansi_code = 16 + (36 * r_scaled) + (6 * g_scaled) + b_scaled
        return f"\033[38;5;{ansi_code}m"

    def interpolate_color(self, factor):
        r = max(0, min(255, int(self.start_color[0] + (self.end_color[0] - self.start_color[0]) * factor)))
        g = max(0, min(255, int(self.start_color[1] + (self.end_color[1] - self.start_color[1]) * factor)))
        b = max(0, min(255, int(self.start_color[2] + (self.end_color[2] - self.start_color[2]) * factor)))
        return r, g, b

    def render_text(self, text):
        rendered_text = self.figlet.renderText(text)
        output = []

        for i, char in enumerate(rendered_text):
            factor = i / max(len(rendered_text) - 1, 1)
            r, g, b = self.interpolate_color(factor)
            output.append(f"{self.rgb_to_ansi(r, g, b)}{char}")

        print("".join(output) + "\033[0m")

    def gettime(self, seconds):
        result = []
        time_units = [(60, "s"), (60, "m"), (24, "h"), (7, "d"), (4.34812, "w")]

        for unit_seconds, suffix in time_units:
            seconds, value = divmod(seconds, unit_seconds)
            if value > 0:
                result.append(f"{int(value)}{suffix}")

        return ":".join(result[::-1]) if result else "0s"

    async def countdown(self, seconds, text="Tunggu {time} untuk melanjutkan", bar_length=30):
        animation_wave = "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁"

        for remaining in range(seconds, -1, -1):
            time_display = self.gettime(remaining)

            progress_color = [self.rgb_to_ansi(*self.interpolate_color(i / bar_length)) for i in range(bar_length)]
            shift = remaining % len(animation_wave)
            bar = "".join(f"{progress_color[i]}{animation_wave[(i + shift) % len(animation_wave)]}" for i in range(bar_length))

            random_text_color = self.rgb_to_ansi(*self.random_color())
            print(f"\033[2K{bar} {random_text_color}{text.format(time=time_display)}\033[0m", end="\r", flush=True)
            await self.asyncio.sleep(1)

    async def ping(self):
        start_time = self.time.perf_counter()
        await self.asyncio.sleep(self.random.uniform(0.1, 0.5))
        end_time = self.time.perf_counter()

        return (end_time - start_time) * 1000
