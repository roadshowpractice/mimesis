import os
import sys
from datetime import datetime

# Adjust path to import helpers
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib")
sys.path.append(lib_path)

import downloader5
from video_utils import initialize_logging, load_app_config
from url_utils import sanitize_instagram_url, detect_host
from tasks_lib import store_params_as_json

# Initialize logging immediately
logger = initialize_logging()

app_config = load_app_config()

def main():
    if len(sys.argv) < 2:
        logger.error("Usage: python call_instagram_download.py <url>")
        sys.exit(1)

    raw_url = sys.argv[1].strip()
    url = sanitize_instagram_url(raw_url)
    host = detect_host(url)
    if host != "instagram":
        logger.warning(f"Expected Instagram URL but detected {host}")

    download_dir = app_config.get("target_usb", ".")
    download_date = datetime.now().strftime("%Y-%m-%d")
    download_path = os.path.join(download_dir, download_date)
    os.makedirs(download_path, exist_ok=True)

    output_file = os.path.join(download_path, "instagram_video.mp4")

    params = {
        "url": url,
        "original_filename": output_file,
        "download_path": download_path,
        "video_download": {},
    }

    result = downloader5.download_video(params)
    if result:
        store_params_as_json(params)
        print(result["to_process"])
    else:
        logger.error("Download failed")

if __name__ == "__main__":
    main()
