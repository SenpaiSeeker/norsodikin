class MarkdownDelimiters:
    BOLD = "**"
    ITALIC = "__"
    UNDERLINE = "--"
    STRIKE = "~~"
    SPOILER = "||"
    CODE = "`"
    PRE = "```"
    BLOCKQUOTE = ">"
    BLOCKQUOTE_EXPANDABLE = "**>"
    BLOCKQUOTE_EXPANDABLE_END = "<**"

class TextFormatter(MarkdownDelimiters):
    def __init__(self, mode: str = "markdown"):
        self.html = __import__("html")
        self._parts = []
        if mode not in ["markdown", "html"]:
            raise ValueError("Mode harus 'markdown' atau 'html'.")
        self.mode = mode

    def text(self, text_content: str):
        if self.mode == "html":
            self._parts.append(self.html.escape(text_content))
        else:
            self._parts.append(text_content)
        return self

    def bold(self, text_content: str):
        if self.mode == "html":
            self._parts.append(f"<b>{self.html.escape(text_content)}</b>")
        else:
            self._parts.append(f"{self.BOLD}{text_content}{self.BOLD}")
        return self

    def italic(self, text_content: str):
        if self.mode == "html":
            self._parts.append(f"<i>{self.html.escape(text_content)}</i>")
        else:
            self._parts.append(f"{self.ITALIC}{text_content}{self.ITALIC}")
        return self
        
    def underline(self, text_content: str):
        if self.mode == "html":
            self._parts.append(f"<u>{self.html.escape(text_content)}</u>")
        else:
            self._parts.append(f"{self.UNDERLINE}{text_content}{self.UNDERLINE}")
        return self

    def strike(self, text_content: str):
        if self.mode == "html":
            self._parts.append(f"<s>{self.html.escape(text_content)}</s>")
        else:
            self._parts.append(f"{self.STRIKE}{text_content}{self.STRIKE}")
        return self
        
    def spoiler(self, text_content: str):
        if self.mode == "html":
            self._parts.append(f"<spoiler>{self.html.escape(text_content)}</spoiler>")
        else:
            self._parts.append(f"{self.SPOILER}{text_content}{self.SPOILER}")
        return self

    def mono(self, text_content: str):
        if self.mode == "html":
            self._parts.append(f"<code>{self.html.escape(text_content)}</code>")
        else:
            self._parts.append(f"{self.CODE}{text_content}{self.CODE}")
        return self
        
    def pre(self, text_content: str):
        if self.mode == "html":
            safe_text = self.html.escape(text_content)
            self._parts.append(f"<pre>{safe_text}</pre>")
        else:
            self._parts.append(f"{self.PRE}\n{text_content}\n{self.PRE}")
        return self

    def blockquote(self, text_content: str):
        if self.mode == "html":
            self._parts.append(f"<blockquote>{self.html.escape(text_content)}</blockquote>")
        else:
            lines = text_content.strip().split('\n')
            formatted_lines = [f"{self.BLOCKQUOTE}{line}" for line in lines]
            self._parts.append("\n".join(formatted_lines))
        return self

    def expandable_blockquote(self, text_content: str):
        if self.mode == "html":
            self._parts.append(f"<blockquote expandable>{self.html.escape(text_content)}</blockquote>")
        else:
            self._parts.append(f"{self.BLOCKQUOTE_EXPANDABLE}{text_content}{self.BLOCKQUOTE_EXPANDABLE_END}")
        return self

    def link(self, text_content: str, url: str):
        if self.mode == "html":
            self._parts.append(f'<a href="{url}">{self.html.escape(text_content)}</a>')
        else:
            self._parts.append(f"[{text_content}]({url})")
        return self

    def new_line(self, count: int = 1):
        self._parts.append("\n" * count)
        return self

    def to_string(self) -> str:
        result = "".join(self._parts)
        self._parts = []
        return result

    def __str__(self):
        return self.to_string()
