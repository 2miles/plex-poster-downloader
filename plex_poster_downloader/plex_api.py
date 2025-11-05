import os
import xml.etree.ElementTree as ET
from typing import Optional

from colorama import Fore, Style
import requests

from .log_utils import (
    bright_magenta_text,
    bright_text,
    log_available_libraries,
    log_fatal_error,
    log_plex_connection_error,
    yellow_text,
)

from .config import PLEX_URL, PLEX_TOKEN


def get_plex_response(endpoint: str, params: dict = None) -> requests.Response:
    """GET wrapper for Plex API with token injection"""
    url = f"{PLEX_URL}{endpoint}"
    if params is None:
        params = {}
    params["X-Plex-Token"] = PLEX_TOKEN

    response = requests.get(url, params=params)
    return response


def get_all_media(id: int) -> Optional[ET.Element]:
    """Fetch all media items from a Plex library section by ID."""
    response = requests.get(f"{PLEX_URL}/library/sections/{id}/all?X-Plex-Token={PLEX_TOKEN}")
    if not response.ok:
        return None
    return ET.fromstring(response.content)


def get_library_metadata(library_id: int) -> Optional[dict]:
    """Returns {'id', 'title', 'type'} for a Plex library section"""
    response = get_plex_response("/library/sections")
    if not response.ok:
        return None

    root = ET.fromstring(response.content)

    for directory in root.findall("Directory"):
        if directory.get("key") == str(library_id):
            return {
                "id": library_id,
                "title": directory.get("title"),
                "type": directory.get("type"),
            }
    return None


def get_library_name(library_id: int) -> Optional[str]:
    """Returns the human-readable name of a Plex library given its numeric ID."""
    response = requests.get(f"{PLEX_URL}/library/sections?X-Plex-Token={PLEX_TOKEN}")
    if not response.ok:
        return None

    root = ET.fromstring(response.content)

    for directory in root.findall("Directory"):
        if directory.get("key") == str(library_id):
            return directory.get("title")

    return None


def list_plex_libraries():
    """Prints a formatted list of Plex libraries (title, type, and ID), sorted by ID."""
    response = get_plex_response("/library/sections")
    if not response.ok:
        log_plex_connection_error(response.status_code, PLEX_URL)

    root = ET.fromstring(response.content)

    libraries = []
    for directory in root.findall("Directory"):
        title = directory.get("title")
        lib_type = directory.get("type")
        lib_id = directory.get("key")
        libraries.append((int(lib_id), title, lib_type))

    libraries.sort()

    log_available_libraries(libraries)


def get_media_path(video_tag: ET.Element) -> Optional[str]:
    """Extracts the directory path of the media file from a Plex metadata XML element."""
    media_tag = video_tag.find("Media")
    if media_tag is None:
        return None

    part_tag = media_tag.find("Part")
    if part_tag is None:
        return None

    file_path = part_tag.get("file")
    if file_path:
        return os.path.dirname(file_path)


def get_path_from_first_episode(show_rating_key: str) -> Optional[str]:
    """Fetch first episode and extract the file path."""
    season_resp = get_plex_response(f"/library/metadata/{show_rating_key}/children")
    if not season_resp.ok:
        return None

    season_root = ET.fromstring(season_resp.content)

    for season in season_root.findall("Directory"):
        season_key = season.get("ratingKey")
        if not season_key:
            continue

        episode_resp = get_plex_response(f"/library/metadata/{season_key}/children")
        if not episode_resp.ok:
            continue

        episode_root = ET.fromstring(episode_resp.content)
        for episode in episode_root.findall("Video"):
            return get_media_path(episode)

    return None


def get_path_from_first_album(artist_rating_key: str) -> Optional[str]:
    """Fetch the first album and extract the file path from its first track."""
    # Get all albums under the artist
    album_resp = get_plex_response(f"/library/metadata/{artist_rating_key}/children")
    if not album_resp.ok:
        return None

    album_root = ET.fromstring(album_resp.content)

    for album in album_root.findall("Directory"):
        album_key = album.get("ratingKey")
        if not album_key:
            continue

        # Fetch tracks (children) inside the album
        track_resp = get_plex_response(f"/library/metadata/{album_key}/children")
        if not track_resp.ok:
            continue

        track_root = ET.fromstring(track_resp.content)
        for track in track_root.findall("Track"):
            return get_media_path(track)

    return None
