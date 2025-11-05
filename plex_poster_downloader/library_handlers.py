import os
import re
import xml.etree.ElementTree as ET

from colorama import Fore, Style

from .artwork import download_artwork, download_image, handle_artwork_download
from .config import PLEX_TOKEN, PLEX_URL
from .file_utils import (
    find_best_match,
    find_matching_folder,
    list_subfolders,
    maybe_rename_folder,
    resolve_nas_path,
    resolve_output_path,
)
from .log_utils import (
    log_invalid_cover_url,
    log_missing_artwork,
    log_missing_media_path,
    log_no_album_cover,
    log_no_folder_match,
    log_nonstandard_season_title,
    log_output_str,
    log_rename_prompt,
)
from .plex_api import (
    get_media_path,
    get_path_from_first_album,
    get_path_from_first_episode,
    get_plex_response,
)
from .utils import increment_counter


def handle_movie_library(root, args, counters):
    for video_tag in root.findall("Video"):
        media_path = get_media_path(video_tag)
        if not media_path:
            title = video_tag.get("title", "Unknown Movie")
            log_missing_media_path(title, "movie")
            continue
        media_path = resolve_nas_path(media_path)
        download_artwork(video_tag, media_path, args, counters)


def handle_show_library(root, args, counters):
    """Main handler for Plex TV show libraries."""
    for show_tag in root.findall("Directory"):
        show_title = show_tag.get("title", "Unknown Show")
        rating_key = show_tag.get("ratingKey")
        if not rating_key:
            return

        # --- Fetch show metadata ---
        show_meta = get_plex_response(f"/library/metadata/{rating_key}")
        if not show_meta.ok:
            return

        meta_root = ET.fromstring(show_meta.content)
        video_tag = meta_root.find("Directory")
        if video_tag is None:
            return

        # --- Resolve show path ---
        media_path = get_path_from_first_episode(rating_key)
        if not media_path:
            log_missing_media_path(show_title, "show")
            continue

        media_path = os.path.dirname(resolve_nas_path(media_path))

        # --- Show-level artwork ---
        download_artwork(video_tag, media_path, args, counters)

        # --- Season-level artwork ---
        handle_show_seasons(rating_key, show_title, media_path, args, counters)


def handle_show_seasons(rating_key, show_title, media_path, args, counters):
    """Handles fetching and matching season-level posters."""
    season_resp = get_plex_response(f"/library/metadata/{rating_key}/children")
    if not season_resp.ok:
        return

    season_root = ET.fromstring(season_resp.content)
    season_root_path = media_path
    folders = list_subfolders(season_root_path)

    for season in season_root.findall("Directory"):
        process_season_tag(season, show_title, season_root_path, folders, args, counters)


def process_season_tag(season, show_title, season_root_path, folders, args, counters):
    """Handle a single season's poster download."""
    season_title = season.get("title", "").strip()
    possible_names = resolve_possible_season_names(season_title)
    if not possible_names:
        return

    matching_folder = find_matching_folder(folders, possible_names)
    if not matching_folder:
        log_no_folder_match(show_title, season_title, season_root_path, "season")
        return

    season_path = os.path.join(season_root_path, matching_folder)

    if args.poster:
        result = handle_artwork_download("poster", season, season_path, args.mode)
        increment_counter(result, counters["poster"])


def resolve_possible_season_names(season_title):
    """Return valid folder name variants for a season title."""
    if season_title.lower() in ["specials", "season 0", "season 00"]:
        return ["Specials", "Season 00", "Season 0"]

    match = re.match(r"Season\s+(\d+)", season_title, re.IGNORECASE)
    if not match:
        if season_title.lower() == "all episodes":
            return None
        log_nonstandard_season_title(season_title)
        return None

    season_num = int(match.group(1))
    return [f"Season {season_num}", f"Season {season_num:02d}"]


def handle_music_library(root, args, counters):
    """Handles downloading artist and album artwork for a Plex music library."""
    for artist_tag in root.findall("Directory"):
        artist_title = artist_tag.get("title", "Unknown Artist")
        artist_key = artist_tag.get("ratingKey")
        if not artist_key:
            return

        artist_path = get_path_from_first_album(artist_key)
        if not artist_path:
            log_missing_media_path(artist_title, "artist")
            continue
        artist_path = resolve_nas_path(os.path.dirname(artist_path))

        handle_artist_artwork(artist_tag, artist_title, artist_path, args, counters)

        if args.poster:
            handle_album_artwork(artist_key, artist_title, artist_path, args, counters)


def handle_artist_artwork(artist_tag, artist_title, artist_path, args, counters):
    if args.poster:
        thumb = artist_tag.get("thumb")
        if thumb:
            result = handle_artwork_download("poster", artist_tag, artist_path, args.mode)
            increment_counter(result, counters["poster"])
        else:
            log_missing_artwork("poster", artist_title)

    if args.fanart:
        art = artist_tag.get("art")
        if art:
            result = handle_artwork_download("fanart", artist_tag, artist_path, args.mode)
            increment_counter(result, counters["fanart"])


def handle_album_artwork(artist_key, artist_title, artist_path, args, counters):
    """Handles album-level cover downloads for a single artist."""
    album_resp = get_plex_response(f"/library/metadata/{artist_key}/children")
    if not album_resp.ok:
        return

    album_root = ET.fromstring(album_resp.content)

    for album_tag in album_root.findall("Directory"):
        process_album_tag(album_tag, artist_title, artist_path, args, counters)


def process_album_tag(album_tag, artist_title, artist_path, args, counters):
    """Processes one album entry"""
    album_title = album_tag.get("title")
    album_thumb = album_tag.get("thumb")

    if not album_thumb:
        log_no_album_cover(album_title, artist_title)
        return

    album_path = os.path.join(artist_path, album_title)

    # Folder matching logic — unchanged
    album_path = resolve_album_path_for_download(
        album_path, artist_title, album_title, artist_path, args
    )
    if not album_path:
        return

    # --- Download cover image (unchanged) ---
    dest_path = resolve_output_path(album_path, args.mode, "cover.jpg")
    if not dest_path:
        increment_counter("skipped", counters["cover"])
        return

    url = f"{PLEX_URL}{album_thumb}?X-Plex-Token={PLEX_TOKEN}"
    if not album_thumb or "None" in url:
        log_invalid_cover_url(album_title, artist_title)
        return

    if not os.path.isdir(os.path.dirname(dest_path)):
        log_missing_media_path(album_title, "album")
        increment_counter("skipped", counters["cover"])
        return

    download_image(url, dest_path)
    log_output_str("cover.jpg", album_title, artist_title, dest_path)
    increment_counter("downloaded", counters["cover"])


def resolve_album_path_for_download(album_path, artist_title, album_title, artist_path, args):
    """Resolve the correct album folder by fuzzy matching and optional renaming."""
    if os.path.isdir(album_path):
        return album_path

    existing_folders = list_subfolders(artist_path)
    match = find_best_match(album_title, existing_folders)

    if not match:
        log_no_folder_match(artist_title, album_title, artist_path, "album")
        return None

    matching_folder = next((f for f in existing_folders if f.lower() == match), None)
    album_path = os.path.join(artist_path, matching_folder)

    if args.rename_albums:
        log_rename_prompt(artist_title, album_title, matching_folder, args.force_rename)
        if matching_folder != album_title:
            renamed = maybe_rename_folder(
                artist_path,
                matching_folder,
                album_title,
                confirm=not args.force_rename,
            )
            if renamed:
                matching_folder = album_title
                album_path = os.path.join(artist_path, matching_folder)

    return album_path
