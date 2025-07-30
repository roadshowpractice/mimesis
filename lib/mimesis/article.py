"""HTML article scraping helpers."""

from __future__ import annotations

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover - fallback if bs4 unavailable
    from html.parser import HTMLParser

    class _PParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.paragraphs: list[str] = []
            self._buf: list[str] = []
            self._capture = False

        def handle_starttag(self, tag, attrs):
            if tag == "p":
                self._capture = True

        def handle_endtag(self, tag):
            if tag == "p" and self._capture:
                text = "".join(self._buf).strip()
                if text:
                    self.paragraphs.append(text)
                self._buf = []
                self._capture = False

        def handle_data(self, data):
            if self._capture:
                self._buf.append(data)

    def _simple_extract(html_content: str) -> list[str]:
        parser = _PParser()
        parser.feed(html_content)
        return parser.paragraphs


def extract_article_text(html_path: str) -> str:
    """Return clean paragraph text from an HTML file."""
    with open(html_path, "r", encoding="utf-8") as file:
        html_content = file.read()
    if "BeautifulSoup" in globals():
        soup = BeautifulSoup(html_content, "html.parser")
        paragraphs = [p.get_text() for p in soup.find_all("p")]
    else:  # fallback parser
        paragraphs = _simple_extract(html_content)

    text_content = "\n\n".join(p for p in paragraphs if p.strip())
    return text_content

