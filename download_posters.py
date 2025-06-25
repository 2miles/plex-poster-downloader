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

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
CONTAINER_MEDIA_PREFIX = os.getenv("CONTAINER_MEDIA_PREFIX", "")
HOST_MEDIA_PREFIX = os.getenv("HOST_MEDIA_PREFIX", "")

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
    response = requests.get(
        f"{PLEX_URL}/library/sections/{id}/all?X-Plex-Token={PLEX_TOKEN}"
    )
    if response.ok:
        root = ET.fromstring(response.content)
        return root
    else:
        return None


def get_media_path(video_tag: ET.Element) -> Optional[str]:
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
    """Converts a media path from inside the Plex container to the corresponding NAS path.
    Returns the original path if no mapping is configured."""

    if (
        CONTAINER_MEDIA_PREFIX
        and HOST_MEDIA_PREFIX
        and container_path.startswith(CONTAINER_MEDIA_PREFIX)
    ):
        return container_path.replace(CONTAINER_MEDIA_PREFIX, HOST_MEDIA_PREFIX, 1)
    return container_path


def get_poster_url(video_tag: ET.Element) -> Optional[str]:
    poster = video_tag.get("thumb")
    if poster:
        return f"{PLEX_URL}{poster}?X-Plex-Token={PLEX_TOKEN}"
    else:
        return None


def next_filename(path: str, mode: str) -> Optional[str]:
    """Determines the appropriate filename to save a poster image, based on the specified mode."""

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
    response = requests.get(poster_url, stream=True)
    if response.status_code == 200:
        with open(path, "wb") as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
    else:
        print(f"Couldn't download poster. Status code: {response.status_code}")


# Fetch all media items from the selected Plex library
root = get_all_media(args.library)
if root is None:
    print(f"Failed to retrieve media for library ID {args.library}")
    exit(1)

# Iterate through each movie in the library
for video_tag in root.findall("Video"):
    # Get the file path of the media item
    media_path = get_media_path(video_tag)
    if not media_path:
        print("The path to the media was not found.")
        continue

    # Convert container path to host path if needed
    media_path = resolve_nas_path(media_path)

    # Determine the appropriate filename based on mode
    poster_path = next_filename(media_path, args.mode)
    if not poster_path:
        print(f"Skipping poster: already exists at {media_path}/poster.jpg")
        continue

    # Get the poster image URL and download it
    poster_url = get_poster_url(video_tag)
    if poster_url:
        print(f"Downloading to: {poster_path}")
        download_poster(poster_url, poster_path)
    else:
        print("No poster URL found.")
