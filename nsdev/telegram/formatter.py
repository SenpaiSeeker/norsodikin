class MarkdownDelimiters:
    BOLD = "**"
    ITALIC = "__"
    UNDERLINE = "--"
    STRIKE = "~~"
    SPOILER = "||"
    CODE = "`"
    PRE = "```"
    BLOCKQUOTE = "> "
    BLOCKQUOTE_ESCAPE = "|> "
    BLOCKQUOTE_EXPANDABLE = "**>"
    BLOCKQUOTE_EXPANDABLE_END = "<**"


class TextFormatter(str, MarkdownDelimiters):
    def __new__(cls, value="", mode="html"):
        return super().__new__(cls, value)

    def __init__(self, value="", mode="html"):
        super().__init__()
        self.mode = mode

    def text(self, text_content: str):
        return TextFormatter(self + str(text_content), mode=self.mode)

    def bold(self, text_content: str):
        if self.mode == "html":
            return TextFormatter(self + f"<b>{text_content}</b>", mode=self.mode)
        return TextFormatter(self + f"{self.BOLD}{text_content}{self.BOLD}", mode=self.mode)

    def italic(self, text_content: str):
        if self.mode == "html":
            return TextFormatter(self + f"<i>{text_content}</i>", mode=self.mode)
        return TextFormatter(self + f"{self.ITALIC}{text_content}{self.ITALIC}", mode=self.mode)

    def underline(self, text_content: str):
        if self.mode == "html":
            return TextFormatter(self + f"<u>{text_content}</u>", mode=self.mode)
        return TextFormatter(self + f"{self.UNDERLINE}{text_content}{self.UNDERLINE}", mode=self.mode)

    def strike(self, text_content: str):
        if self.mode == "html":
            return TextFormatter(self + f"<s>{text_content}</s>", mode=self.mode)
        return TextFormatter(self + f"{self.STRIKE}{text_content}{self.STRIKE}", mode=self.mode)

    def spoiler(self, text_content: str):
        if self.mode == "html":
            return TextFormatter(self + f"<spoiler>{text_content}</spoiler>", mode=self.mode)
        return TextFormatter(self + f"{self.SPOILER}{text_content}{self.SPOILER}", mode=self.mode)

    def mono(self, text_content: str):
        if self.mode == "html":
            return TextFormatter(self + f"<code>{text_content}</code>", mode=self.mode)
        return TextFormatter(self + f"{self.CODE}{text_content}{self.CODE}", mode=self.mode)

    def pre(self, text_content: str, language: str = ""):
        if self.mode == "html":
            return TextFormatter(
                self + f"<pre><code class='language-{language}'>{text_content}</code></pre>", mode=self.mode
            )
        return TextFormatter(self + f"{self.PRE}{language}\n{text_content}\n{self.PRE}", mode=self.mode)

    def blockquote(self, text_content: str):
        if self.mode == "html":
            return TextFormatter(self + f"<blockquote>{text_content}</blockquote>", mode=self.mode)

        lines = str(text_content).strip().split("\n")
        quoted_lines = "\n".join(f"{self.BLOCKQUOTE}{line}" for line in lines)
        return TextFormatter(self + quoted_lines, mode=self.mode)

    def escaped_blockquote(self, text_content: str):
        if self.mode == "html":
            return self.blockquote(text_content)

        lines = str(text_content).strip().split("\n")
        quoted_lines = "\n".join(f"{self.BLOCKQUOTE_ESCAPE}{line}" for line in lines)
        return TextFormatter(self + quoted_lines, mode=self.mode)

    def expandable_blockquote(self, text_content: str):
        if self.mode == "html":
            return TextFormatter(self + f"<blockquote expandable>{text_content}</blockquote>", mode=self.mode)
        return TextFormatter(
            self + f"{self.BLOCKQUOTE_EXPANDABLE}{text_content}{self.BLOCKQUOTE_EXPANDABLE_END}", mode=self.mode
        )

    def link(self, text_content: str, url: str):
        if self.mode == "html":
            return TextFormatter(self + f'<a href="{url}">{text_content}</a>', mode=self.mode)
        return TextFormatter(self + f"[{text_content}]({url})", mode=self.mode)

    def new_line(self, count: int = 1):
        return TextFormatter(self + ("\n" * count), mode=self.mode)
