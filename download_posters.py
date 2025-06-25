"""
This script is adapted from an original version by Paul Salmon (TechieGuy12),
available via https://www.plexopedia.com/blog/download-movie-posters-from-plex-server/

Significant modifications and enhancements were made to support poster naming modes,
environment-based configuration, error handling, and improved documentation.
"""

import argparse
from dotenv import load_dotenv
from typing import Optional
import os
import requests
import shutil
import xml.etree.ElementTree as ET

load_dotenv()

PLEX_URL = os.environ.get("PLEX_URL")
PLEX_TOKEN = os.environ.get("PLEX_TOKEN")

CONTAINER_MEDIA_PREFIX = os.getenv("PLEX_MEDIA_PREFIX", "")
HOST_MEDIA_PREFIX = os.getenv("NAS_MEDIA_PREFIX", "")

parser = argparse.ArgumentParser(description="Download Plex posters.")
parser.add_argument(
    "--mode",
    choices=["skip", "overwrite", "add"],
    default="skip",
    help="Poster handling mode: skip (default), overwrite, or add new poster file",
)
parser.add_argument(
    "--library",
    type=int,
    default=1,
    help="Plex library section ID to pull posters from (default: 1)",
)
args = parser.parse_args()


def get_all_media(id: int) -> Optional[ET.Element]:
    """
    Retrieves all media items from a specified Plex library.

    Args:
        id (int): The numeric ID of the Plex library.

    Returns:
        Optional[Element]: The root XML element if successful, otherwise None.
    """
    response = requests.get(
        f"{PLEX_URL}/library/sections/{id}/all?X-Plex-Token={PLEX_TOKEN}"
    )
    if response.ok:
        root = ET.fromstring(response.content)
        return root
    else:
        return None


def get_media_path(video_tag: ET.Element) -> Optional[str]:
    """
    Returns the directory path for a media item, based on its metadata.

    Args:
        video_tag (Element): A *Video* tag from the Plex API XML.

    Returns:
        Optional[str]: The folder path where the poster should be saved,
        or None if the path couldn't be determined.
    """
    media_tag = video_tag.find("Media")
    if media_tag is None:
        return None

    part_tag = media_tag.find("Part")
    if part_tag is None:
        return None

    file_path = part_tag.get("file")
    if file_path:
        return os.path.dirname(file_path)


def resolve_nas_path(container_path: str) -> str:
    """
    Converts a media path inside the Plex container to the corresponding NAS filesystem path.
    If PLEX_MEDIA_PREFIX or NAS_MEDIA_PREFIX is not set, returns the original path.

    Args:
        container_path (str): The original path from Plex (e.g., "/data/media/...")

    Returns:
        str: The adjusted path for the NAS host (e.g., "/volume1/data/media/..."), or the original path if not modified.
    """
    if (
        CONTAINER_MEDIA_PREFIX
        and HOST_MEDIA_PREFIX
        and container_path.startswith(CONTAINER_MEDIA_PREFIX)
    ):
        return container_path.replace(CONTAINER_MEDIA_PREFIX, HOST_MEDIA_PREFIX, 1)
    return container_path


def get_poster_url(video_tag: ET.Element) -> Optional[str]:
    """
    Constructs the URL to download a media item's poster from Plex.

    Args:
        video_tag (Element): A Video XML tag from the Plex API.

    Returns:
        Optional[str]: The full poster URL if available, otherwise None.
    """

    poster = video_tag.get("thumb")
    if poster:
        return f"{PLEX_URL}{poster}?X-Plex-Token={PLEX_TOKEN}"
    else:
        return None


def next_filename(path: str, mode: str) -> Optional[str]:
    """
    Determines the appropriate filename to save a poster image, based on the specified mode.

    Args:
        path (str): The directory path where the poster should be saved.
        mode (str): Poster saving mode. One of:
            - skip: "Only use poster.jpg if it doesn't already exist."
            - overwrite: "Always use 'poster.jpg', replacing any existing file."
            - add: "Always create a new poster file (e.g., 'poster-1.jpg', 'poster-2.jpg', etc.)."

    Returns:
        Optional[str]: The resolved poster file path to use, or None if skipped.
    """

    base_path = f"{path}/poster.jpg"

    if mode == "overwrite":
        return base_path

    if mode == "skip":
        return base_path if not os.path.exists(base_path) else None

    if mode == "add":
        if not os.path.exists(base_path):
            return base_path

        i = 1
        while True:
            new_path = f"{path}/poster-{i}.jpg"
            if not os.path.exists(new_path):
                return new_path
            i += 1

    return None


def download_poster(poster_url: str, path: str) -> None:
    """
    Downloads the poster image from the given URL and saves it to the specified path.

    Args:
        poster_url (str): The full URL of the poster image to download.
        path (str): The local file path where the poster should be saved.

    Returns:
        None
    """
    response = requests.get(poster_url, stream=True)
    if response.status_code == 200:
        with open(path, "wb") as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
    else:
        print(f"Couldn't download poster. Status code: {response.status_code}")


root = get_all_media(args.library)
if root is None:
    print(f"Failed to retrieve media for library ID {args.library}")
    exit(1)

for video_tag in root.findall("Video"):
    media_path = get_media_path(video_tag)
    if not media_path:
        print("The path to the media was not found.")
        continue
    media_path = resolve_nas_path(media_path)
    poster_path = next_filename(media_path, args.mode)
    if not poster_path:
        print(f"Skipping poster: already exists at {media_path}/poster.jpg")
        continue

    poster_url = get_poster_url(video_tag)
    if poster_url:
        print(f"Downloading to: {poster_path}")
        download_poster(poster_url, poster_path)
    else:
        print("No poster URL found.")
