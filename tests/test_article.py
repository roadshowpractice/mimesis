from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "lib"))

from mimesis.article import extract_article_text


def test_extract_article_text(tmp_path):
    html_content = """
    <html><body>
        <p>First paragraph.</p>
        <div>ignored</div>
        <p>Second paragraph.</p>
    </body></html>
    """
    html_file = tmp_path / "test.html"
    html_file.write_text(html_content, encoding="utf-8")

    text = extract_article_text(str(html_file))
    assert text == "First paragraph.\n\nSecond paragraph."

