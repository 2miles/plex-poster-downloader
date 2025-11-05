import os
import shutil
from typing import Literal, Optional
import xml.etree.ElementTree as ET

import requests

from .config import PLEX_TOKEN, PLEX_URL
from .file_utils import resolve_output_path
from .utils import increment_counter
from .log_utils import log_failed_image_download, log_missing_artwork, log_output_str


def get_image_url(image_type: str, video_tag: ET.Element) -> Optional[str]:
    """Constructs the full URL to download the fanart or poster for a media item."""
    if image_type == "poster":
        image = video_tag.get("thumb")
    elif image_type == "fanart":
        image = video_tag.get("art")
    else:
        return None

    if not image or image == "None":
        return None

    return f"{PLEX_URL}{image}?X-Plex-Token={PLEX_TOKEN}"


def download_image(poster_url: str, path: str) -> bool:
    """Download an image from a given URL and save it to the specified local path."""
    try:
        response = requests.get(poster_url, stream=True, timeout=15)
        if not response.ok:
            return False

        with open(path, "wb") as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
        return True

    except (requests.RequestException, OSError):
        return False


def handle_artwork_download(
    kind: Literal["poster", "fanart"],
    video_tag: ET.Element,
    media_path: str,
    mode: Literal["overwrite", "skip", "add"],
) -> Literal["downloaded", "skipped", "none"]:
    """
    Downloads a poster or fanart image for a media item if a valid URL and path are available.
    """
    url = get_image_url(kind, video_tag)
    filename = f"{kind}.jpg"
    dest_path = resolve_output_path(media_path, mode, filename)
    title = video_tag.get("title", "Unknown Title")
    show_name = video_tag.get("parentTitle", title)

    if not url:
        if kind == "poster":
            log_missing_artwork("poster", title)
        return "none"

    if not dest_path:
        return "skipped"

    success = download_image(url, dest_path)
    if not success:
        log_failed_image_download(kind, title)
        return "skipped"
    log_output_str(filename, title, show_name, dest_path)
    return "downloaded"


def download_artwork(tag, path, args, counters):
    if args.poster:
        result = handle_artwork_download("poster", tag, path, args.mode)
        increment_counter(result, counters["poster"])
    if args.fanart:
        result = handle_artwork_download("fanart", tag, path, args.mode)
        increment_counter(result, counters["fanart"])
