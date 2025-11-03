import os
import shutil
from typing import Literal, Optional
import xml.etree.ElementTree as ET

import requests

from .config import PLEX_TOKEN, PLEX_URL
from .file_utils import resolve_output_path
from .utils import increment_counter
from .log_utils import log_output_str


def get_image_url(image_type: str, video_tag: ET.Element) -> Optional[str]:
    """Constructs the full URL to download the fanart or poster for a media item."""
    if image_type == "poster":
        image = video_tag.get("thumb")
    elif image_type == "fanart":
        image = video_tag.get("art")
    else:
        return None

    # Guard: return None if Plex didn't provide a valid path
    if not image or image == "None":
        return None

    return f"{PLEX_URL}{image}?X-Plex-Token={PLEX_TOKEN}"


def download_image(poster_url: str, path: str):
    """Downloads an image from a given URL and saves it to the specified local path."""
    response = requests.get(poster_url, stream=True)
    if response.status_code == 200:
        with open(path, "wb") as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
    else:
        print(f"Couldn't download poster. Status code: {response.status_code}")


def handle_artwork_download(
    kind: Literal["poster", "fanart"],
    video_tag: ET.Element,
    media_path: str,
    mode: Literal["overwrite", "skip", "add"],
) -> Literal["downloaded", "skipped", "none"]:
    """Downloads a poster or fanart image for a media item if a valid URL and path are available."""
    url = get_image_url(kind, video_tag)
    filename = f"{kind}.jpg"
    dest_path = resolve_output_path(media_path, mode, filename)
    title = video_tag.get("title", "Unknown Title")
    show_name = video_tag.get("parentTitle", title)

    ###########
    # Use logger for fanart and other warnings, unless --verbose is set
    ###########
    # if not url:
    #     print(f"[WARN] No {kind} URL found for '{title}'")
    #     return "none"
    if not url:
        if kind == "poster":
            print(f"[WARN] No poster URL found for '{title}'")
        return "none"

    if not dest_path:
        return "skipped"

    download_image(url, dest_path)
    log_output_str(filename, title, show_name, dest_path)
    return "downloaded"


def download_artwork(tag, path, args, counters):
    if args.poster:
        result = handle_artwork_download("poster", tag, path, args.mode)
        increment_counter(result, counters["poster"])
    if args.fanart:
        result = handle_artwork_download("fanart", tag, path, args.mode)
        increment_counter(result, counters["fanart"])


def download_image_if_needed(url: str, dest_path: str, args) -> bool:
    """
    Downloads an image only if necessary, depending on the selected mode.
    Returns True if the image was downloaded, False if skipped.
    """
    if not url or not dest_path:
        return False

    # Skip if file already exists and mode says skip
    if args.mode == "skip" and os.path.exists(dest_path):
        title = os.path.basename(os.path.dirname(dest_path))
        print(f"Skipping poster: {title}")
        return False

    # Skip if 'add' mode and file already exists
    if args.mode == "add" and os.path.exists(dest_path):
        return False

    response = requests.get(url, stream=True)
    if not response.ok:
        print(f"Failed to download: {url}")
        return False

    with open(dest_path, "wb") as f:
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, f)

    return True
