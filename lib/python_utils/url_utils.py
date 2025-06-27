import re
from urllib.parse import urlparse, parse_qs


def sanitize_facebook_url(url: str) -> str:
    """Return a simplified Facebook video URL if possible."""
    parsed = urlparse(url)

    # Query parameter based share URLs
    qs = parse_qs(parsed.query)
    vid = None
    if "v" in qs and qs["v"]:
        vid = qs["v"][0]
    else:
        m = re.search(r"/v/([0-9A-Za-z]+)", parsed.path)
        if m:
            vid = m.group(1)

    if not vid:
        return url

    return f"https://www.facebook.com/watch/?v={vid}"


def detect_host(url: str) -> str:
    """Return a short name describing the hosting platform for ``url``."""
    host = urlparse(url).netloc.lower()
    if "facebook.com" in host:
        return "facebook"
    elif "instagram.com" in host:
        return "instagram"
    elif "youtube.com" in host or "youtu.be" in host:
        return "youtube"
    elif "google.com" in host or "googleusercontent.com" in host:
        return "google_drive"
    return "unknown"
