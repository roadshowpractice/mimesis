from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "lib" / "python_utils"))

from url_utils import sanitize_facebook_url


def test_sanitize_facebook_url():
    messy = "https://www.facebook.com/share/v/12345/?mibextid=abc&__tn__=R"
    assert sanitize_facebook_url(messy) == "https://www.facebook.com/watch/?v=12345"

    simple = "https://www.facebook.com/watch/?v=6789"
    assert sanitize_facebook_url(simple) == simple

