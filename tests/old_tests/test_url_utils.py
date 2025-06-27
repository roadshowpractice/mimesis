from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "lib"))

from url_utils import sanitize_facebook_url, detect_host


def test_sanitize_facebook_url():
    messy = "https://www.facebook.com/share/v/12345/?mibextid=abc&__tn__=R"
    assert sanitize_facebook_url(messy) == "https://www.facebook.com/watch/?v=12345"

    simple = "https://www.facebook.com/watch/?v=6789"
    assert sanitize_facebook_url(simple) == simple


def test_detect_host():
    assert detect_host("https://www.facebook.com/watch?v=123") == "facebook"
    assert detect_host("https://www.instagram.com/reel/abc") == "instagram"
    assert detect_host("https://youtu.be/xyz") == "youtube"
    assert detect_host("https://drive.google.com/file/d/123") == "google_drive"
    assert detect_host("https://example.com") == "unknown"

