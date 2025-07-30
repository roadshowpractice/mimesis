#!/usr/bin/env python3
"""Extract plain text from an HTML article."""

import json
import os
from pathlib import Path

from mimesis.article import extract_article_text


def main() -> None:
    """Load paths from input.json and write extracted text."""
    with open("input.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    html_path = data["html_file_path"]
    output_path = data["output_file_path"]

    article_text = extract_article_text(html_path)
    result = {
        "article_text": article_text[:1500]
        + ("..." if len(article_text) > 1500 else "")
    }

    os.makedirs(Path(output_path).parent, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()
