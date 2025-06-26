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
