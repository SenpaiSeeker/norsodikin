class MarkdownDelimiters:
    BOLD = "**"
    ITALIC = "__"
    UNDERLINE = "--"
    STRIKE = "~~"
    SPOILER = "||"
    CODE = "`"
    PRE = "```"
    BLOCKQUOTE = ">"
    BLOCKQUOTE_ESCAPE = "|>"
    BLOCKQUOTE_EXPANDABLE = "**>"
    BLOCKQUOTE_EXPANDABLE_END = "<**"


class TextFormatter(MarkdownDelimiters):
    def __init__(self, mode: str = "markdown"):
        self.html = __import__("html")
        self._parts = []
        if mode not in ["markdown", "html"]:
            raise ValueError("Mode harus 'markdown' atau 'html'.")
        self.mode = mode

    def _process_content(self, content):
        if isinstance(content, TextFormatter):
            return content.to_string()

        text_content = str(content)
        if self.mode == "html":
            return self.html.escape(text_content)
        return text_content

    def text(self, text_content: str):
        self._parts.append(self._process_content(text_content))
        return self

    def bold(self, text_content: str):
        processed = self._process_content(text_content)
        if self.mode == "html":
            self._parts.append(f"<b>{processed}</b>")
        else:
            self._parts.append(f"{self.BOLD}{processed}{self.BOLD}")
        return self

    def italic(self, text_content: str):
        processed = self._process_content(text_content)
        if self.mode == "html":
            self._parts.append(f"<i>{processed}</i>")
        else:
            self._parts.append(f"{self.ITALIC}{processed}{self.ITALIC}")
        return self

    def underline(self, text_content: str):
        processed = self._process_content(text_content)
        if self.mode == "html":
            self._parts.append(f"<u>{processed}</u>")
        else:
            self._parts.append(f"{self.UNDERLINE}{processed}{self.UNDERLINE}")
        return self

    def strike(self, text_content: str):
        processed = self._process_content(text_content)
        if self.mode == "html":
            self._parts.append(f"<s>{processed}</s>")
        else:
            self._parts.append(f"{self.STRIKE}{processed}{self.STRIKE}")
        return self

    def spoiler(self, content):
        inner_text = self._process_content(content)
        if self.mode == "html":
            self._parts.append(f"<tg-spoiler>{inner_text}</tg-spoiler>")
        else:
            self._parts.append(f"{self.SPOILER}{inner_text}{self.SPOILER}")
        return self

    def mono(self, text_content: str):
        processed = self._process_content(text_content)
        if self.mode == "html":
            self._parts.append(f"<code>{processed}</code>")
        else:
            self._parts.append(f"{self.CODE}{processed}{self.CODE}")
        return self

    def pre(self, content):
        inner_text = self._process_content(content)
        if self.mode == "html":
            self._parts.append(f"<pre><code>{inner_text}</code></pre>")
        else:
            self._parts.append(f"{self.PRE}\n{inner_text}\n{self.PRE}")
        return self

    def blockquote(self, content):
        inner_text = self._process_content(content)
        if self.mode == "html":
            self._parts.append(f"<blockquote>{inner_text}</blockquote>")
        else:
            lines = inner_text.strip().split("\n")
            formatted_lines = [f"{self.BLOCKQUOTE} {line}" for line in lines]
            self._parts.append("\n".join(formatted_lines))
        return self

    def escaped_blockquote(self, content):
        inner_text = self._process_content(content)
        if self.mode == "html":
            self._parts.append(f"<blockquote>{inner_text}</blockquote>")
        else:
            lines = inner_text.strip().split("\n")
            formatted_lines = [f"{self.BLOCKQUOTE_ESCAPE} {line}" for line in lines]
            self._parts.append("\n".join(formatted_lines))
        return self

    def expandable_blockquote(self, content):
        inner_text = self._process_content(content)
        if self.mode == "html":
            self._parts.append(f"<blockquote expandable>{inner_text}</blockquote>")
        else:
            self._parts.append(f"{self.BLOCKQUOTE_EXPANDABLE}{inner_text}{self.BLOCKQUOTE_EXPANDABLE_END}")
        return self

    def link(self, text_content: str, url: str):
        processed = self._process_content(text_content)
        if self.mode == "html":
            self._parts.append(f'<a href="{url}">{processed}</a>')
        else:
            self._parts.append(f"[{processed}]({url})")
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
