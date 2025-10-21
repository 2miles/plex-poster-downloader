"""
This script is adapted from an original version by Paul Salmon (TechieGuy12),
available via https://www.plexopedia.com/blog/download-movie-posters-from-plex-server/

Significant modifications and enhancements were made to support poster naming modes,
environment-based configuration, error handling, and improved documentation.
"""

import argparse
from dotenv import load_dotenv
import os
import re
import requests
import shutil
from typing import Optional
import xml.etree.ElementTree as ET

try:
    from colorama import Fore, Style, init

    init(autoreset=True)
except ImportError:

    class Dummy:
        def __getattr__(self, _):
            return ""

    Fore = Style = Dummy()

init(autoreset=True)

load_dotenv()

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
CONTAINER_MEDIA_PREFIX = os.getenv("CONTAINER_MEDIA_PREFIX", "")
HOST_MEDIA_PREFIX = os.getenv("HOST_MEDIA_PREFIX", "")


def check_required_env():
    """
    Checks that all required environment variables are set, and exits with an error if any are
    missing.
    """
    missing = []
    if not PLEX_URL:
        missing.append("PLEX_URL")
    if not PLEX_TOKEN:
        missing.append("PLEX_TOKEN")
    if missing:
        print(f"Error: Missing environment variable(s): {', '.join(missing)}")
        print("Please set them in your .env file.")
        exit(1)


def get_all_media(id: int) -> Optional[ET.Element]:
    """Fetches all media items from a Plex library section by ID."""
    response = requests.get(f"{PLEX_URL}/library/sections/{id}/all?X-Plex-Token={PLEX_TOKEN}")
    if response.ok:
        root = ET.fromstring(response.content)
        return root
    else:
        return None


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
    """Constructs the full URL to download the poster for a media item."""
    poster = video_tag.get("thumb")
    if poster:
        return f"{PLEX_URL}{poster}?X-Plex-Token={PLEX_TOKEN}"
    else:
        return None


def get_fanart_url(video_tag: ET.Element) -> Optional[str]:
    """Constructs the full URL to download the fanart for a media item."""
    art = video_tag.get("art")
    if art:
        return f"{PLEX_URL}{art}?X-Plex-Token={PLEX_TOKEN}"
    else:
        return None


def resolve_output_path(path: str, mode: str, basename: str = "poster.jpg") -> Optional[str]:
    """Determines the appropriate filename to save an image, based on the specified mode."""

    base_path = os.path.join(path, basename)

    if mode == "overwrite":
        return base_path
    if mode == "skip":
        return base_path if not os.path.exists(base_path) else None
    if mode == "add":
        if not os.path.exists(base_path):
            return base_path
        name, ext = os.path.splitext(basename)
        i = 1
        while True:
            new_path = os.path.join(path, f"{name}-{i}{ext}")
            if not os.path.exists(new_path):
                return new_path
            i += 1
    return None


def download_image(poster_url: str, path: str) -> None:
    """Downloads an image from a given URL and saves it to the specified local path."""
    response = requests.get(poster_url, stream=True)
    if response.status_code == 200:
        with open(path, "wb") as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
    else:
        print(f"Couldn't download poster. Status code: {response.status_code}")


def log_output_str(filename, title, dest_path) -> str:
    """Prints a formatted success message when an image is downloaded."""
    parent_folder = os.path.basename(os.path.dirname(dest_path))

    # Case-insensitive match for folders like "Season 1", "Season 01", etc.
    is_season_folder = re.match(r"(?i)^season\s+\d+$", parent_folder)

    if filename == "fanart.jpg":
        print(
            f"{Fore.GREEN}Downloading {Fore.LIGHTCYAN_EX}{filename}{Style.RESET_ALL} {Fore.WHITE}for "
            f"{Style.BRIGHT}{Fore.WHITE}'{title}'{Style.RESET_ALL} {Fore.WHITE}→ {Fore.BLUE}{dest_path}"
        )
    elif filename == "poster.jpg":
        location_type = "season" if is_season_folder else "show"
        if location_type == "show":
            print(
                f"{Fore.GREEN}Downloading {Fore.CYAN}{filename}{Style.RESET_ALL} "
                f"{Fore.WHITE} {Style.BRIGHT}{Fore.WHITE}'{title}'{Style.RESET_ALL} "
                f"{Fore.WHITE}→ {Fore.BLUE}{dest_path}"
            )
        if location_type == "season":
            print(
                f"{Fore.GREEN}Downloading {Fore.CYAN}{filename}{Style.RESET_ALL} "
                f"{Fore.WHITE}'{title}'"
                f"{Fore.WHITE}→ {Fore.BLUE}{dest_path}"
            )


def handle_artwork_download(kind, video_tag, media_path, mode):
    """
    Handles downloading either a poster or fanart image for a media item.

    Args:
        kind: 'poster' or 'fanart'
        video_tag: Plex metadata XML element
        media_path: filesystem path to save the image
        mode: overwrite / skip / add
    """
    get_url = get_poster_url if kind == "poster" else get_fanart_url
    filename = "poster.jpg" if kind == "poster" else "fanart.jpg"

    url = get_url(video_tag)
    dest_path = resolve_output_path(media_path, mode, filename)

    title = video_tag.get("title", "Unknown Title")

    if not dest_path and mode == "skip":
        return "skipped"
    elif url and dest_path:
        download_image(url, dest_path)
        log_output_str(filename, title, dest_path)
        return "downloaded"
    return "none"


def get_library_name(library_id: int) -> Optional[str]:
    """Returns the human-readable name of a Plex library given its numeric ID."""
    response = requests.get(f"{PLEX_URL}/library/sections?X-Plex-Token={PLEX_TOKEN}")
    if response.ok:
        root = ET.fromstring(response.content)
        for directory in root.findall("Directory"):
            if directory.get("key") == str(library_id):
                return directory.get("title")
    return None


def get_plex_response(endpoint: str, params: dict = None) -> requests.Response:
    """
    Makes a raw GET request to a Plex API endpoint and returns the response object.

    Args:
        endpoint (str): The API path, e.g. "/library/sections"
        params (dict, optional): Additional query parameters.

    Returns:
        requests.Response: The raw response object from the Plex API.
    """
    url = f"{PLEX_URL}{endpoint}"
    if params is None:
        params = {}
    params["X-Plex-Token"] = PLEX_TOKEN

    response = requests.get(url, params=params)
    return response


def get_library_metadata(library_id: int) -> Optional[dict]:
    """
    Returns metadata for a Plex library by ID, including title and type.

    Returns:
        dict with 'id', 'title', and 'type', or None if not found.
    """
    response = get_plex_response("/library/sections")
    if response.ok:
        root = ET.fromstring(response.content)
        for directory in root.findall("Directory"):
            if directory.get("key") == str(library_id):
                return {
                    "id": library_id,
                    "title": directory.get("title"),
                    "type": directory.get("type"),
                }
    return None


def get_path_from_first_episode(show_rating_key: str) -> Optional[str]:
    """
    Given a show's rating key, fetches its first episode and extracts the file path.
    """
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
    path = get_media_path(episode)
    return None


def list_plex_libraries():
    """
    Fetches and prints a formatted list of Plex libraries (title, type, and ID), sorted by ID.
    """
    response = get_plex_response("/library/sections")
    if not response.ok:
        print(f"Failed to fetch libraries: {response.status_code}")
        return

    root = ET.fromstring(response.content)

    # Collect libraries into a list of tuples
    libraries = []
    for directory in root.findall("Directory"):
        title = directory.get("title")
        lib_type = directory.get("type")
        lib_id = directory.get("key")
        libraries.append((int(lib_id), title, lib_type))

    # Sort by lib_id (numeric)
    libraries.sort()

    print(
        f"\n\n{Style.BRIGHT}Available Plex Libraries:"
        f"\n{Style.BRIGHT}{Fore.WHITE}==============================================================="
    )

    for lib_id, title, lib_type in libraries:
        print(
            f"{Style.BRIGHT}{Fore.MAGENTA}{title:<30}{Style.RESET_ALL}"
            f"{Fore.YELLOW}type: {lib_type:<8}  "
            f"{Fore.WHITE}library: {Style.BRIGHT}{lib_id}"
        )
    print("\n")


def print_summary(
    args,
    library_name,
    poster_downloaded,
    poster_skipped,
    fanart_downloaded,
    fanart_skipped,
):
    """Prints a summary of how many posters/fanart images were downloaded or skipped."""
    if args.posters or args.fanart:
        print(
            f"\n{Style.BRIGHT}Download Summary for Library: {Fore.MAGENTA}{library_name}"
            f"\n{Fore.WHITE}==============================================================="
        )
        if args.posters:
            print(f"Posters downloaded: {Style.BRIGHT}{poster_downloaded}")
            if args.mode == "skip":
                print(f"Posters skipped: {Style.BRIGHT}{poster_skipped}")
        if args.fanart:
            print(f"Fanart downloaded: {Style.BRIGHT}{fanart_downloaded}")
            if args.mode == "skip":
                print(f"Fanart skipped: {Style.BRIGHT}{fanart_skipped}")
        print("\n\n")


# ==================================================================================================
# Main Entry Point
# ==================================================================================================


def main():
    check_required_env()

    # =========================
    # Argument Parsing
    # =========================

    parser = argparse.ArgumentParser(
        description="""
    Download poster.jpg and/or fanart.jpg for media items from a Plex library.

    Supports configurable overwrite modes, per-artwork-type toggling, and results summary.

    Use --list-libraries to view available libraries before downloading.

    Examples:
    python download_posters.py --list-libraries
    python download_posters.py --posters --fanart
    python download_posters.py --library 3 --posters
    python download_posters.py --library 4 --mode overwrite --fanart
    python download_posters.py --library 2 --mode add --posters --fanart
    """,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--mode",
        choices=["skip", "overwrite", "add"],
        default="skip",
        help="File handling mode: 'skip' (default) skips existing files, 'overwrite' replaces them, 'add' creates additional versions like poster-1.jpg.",
    )
    parser.add_argument(
        "--library",
        type=int,
        default=1,
        help="Plex library section ID to pull artwork from (default: 1)",
    )

    parser.add_argument(
        "--posters",
        action="store_true",
        default=False,
        help="Enable poster downloading.",
    )

    parser.add_argument(
        "--fanart",
        action="store_true",
        default=False,
        help="Enable fanart downloading.",
    )

    parser.add_argument(
        "--list-libraries",
        action="store_true",
        default=False,
        help="List available plex library id's.",
    )

    args = parser.parse_args()

    # =========================
    # Download Images
    # =========================

    library = get_library_metadata(args.library)
    if not library:
        print(f"Failed to retrieve metadata ofr library ID {args.library}")
        exit(1)

    library_name = library["title"]
    library_type = library["type"]

    root = get_all_media(args.library)
    if root is None:
        print(f"Failed to retrieve media for library ID {args.library}")
        exit(1)

    poster_skipped = poster_downloaded = 0
    fanart_skipped = fanart_downloaded = 0

    if library_type == "movie":
        for video_tag in root.findall("Video"):
            media_path = get_media_path(video_tag)
            if not media_path:
                print("The path to the media was not found.")
                continue
            media_path = resolve_nas_path(media_path)

            if args.posters:
                result = handle_artwork_download("poster", video_tag, media_path, args.mode)
                if result == "skipped":
                    poster_skipped += 1
                elif result == "downloaded":
                    poster_downloaded += 1

            if args.fanart:
                result = handle_artwork_download("fanart", video_tag, media_path, args.mode)
                if result == "skipped":
                    fanart_skipped += 1
                elif result == "downloaded":
                    fanart_downloaded += 1

    elif library_type == "show":
        for show_tag in root.findall("Directory"):
            show_title = show_tag.get("title", "Unknown Show")
            rating_key = show_tag.get("ratingKey")
            if not rating_key:
                continue

            # Fetch metadata to get poster
            show_meta = get_plex_response(f"/library/metadata/{rating_key}")
            if not show_meta.ok:
                continue
            meta_root = ET.fromstring(show_meta.content)
            video_tag = meta_root.find("Directory")
            if video_tag is None:
                continue

            # 2. Resolve media path (based on first episode)
            media_path = get_path_from_first_episode(rating_key)
            if not media_path:
                print(f"Could not resolve path for show: {show_title}")
                continue
            media_path = os.path.dirname(resolve_nas_path(media_path))

            if args.posters:
                result = handle_artwork_download("poster", video_tag, media_path, args.mode)
                if result == "skipped":
                    poster_skipped += 1
                elif result == "downloaded":
                    poster_downloaded += 1

            if args.fanart:
                result = handle_artwork_download("fanart", video_tag, media_path, args.mode)
                if result == "skipped":
                    fanart_skipped += 1
                elif result == "downloaded":
                    fanart_downloaded += 1

            # 3. Season-level poster download
            season_resp = get_plex_response(f"/library/metadata/{rating_key}/children")
            if season_resp.ok:
                season_root = ET.fromstring(season_resp.content)
                season_root_path = media_path

                try:
                    folders = [
                        d
                        for d in os.listdir(season_root_path)
                        if os.path.isdir(os.path.join(season_root_path, d))
                    ]
                except FileNotFoundError:
                    print(f"[ERROR] Could not list folders in {season_root_path}")
                    folders = []

                for season in season_root.findall("Directory"):

                    season_title = season.get("title", "").strip()

                    # Only handle "Season X" style titles
                    match = re.match(r"Season\s+(\d+)", season_title, re.IGNORECASE)
                    if not match:
                        if season_title.lower() == "all episodes":
                            continue
                        print(f"[WARN] Skipping non-standard season title: '{season_title}'")
                        continue

                    season_num = int(match.group(1))
                    possible_names = [f"Season {season_num}", f"Season {season_num:02d}"]

                    # Read folders once
                    try:
                        folders = [
                            d
                            for d in os.listdir(season_root_path)
                            if os.path.isdir(os.path.join(season_root_path, d))
                        ]
                    except FileNotFoundError:
                        print(f"[ERROR] Could not list folders in {season_root_path}")
                        folders = []

                    # Try to find a match in folder names (case-insensitive)
                    matching_folder = next(
                        (
                            f
                            for f in folders
                            if f.lower() in [name.lower() for name in possible_names]
                        ),
                        None,
                    )

                    if matching_folder:
                        season_path = os.path.join(season_root_path, matching_folder)
                    else:
                        print(f"[WARN] No folder matched season '{season_title}'")
                        continue

                    if args.posters:
                        result = handle_artwork_download("poster", season, season_path, args.mode)
                        if result == "skipped":
                            poster_skipped += 1
                        elif result == "downloaded":
                            poster_downloaded += 1
    else:
        print(f"Unsupported library type: {library_type}")

    if args.list_libraries:
        list_plex_libraries()

    # =========================
    # Summary Output
    # =========================

    print_summary(
        args,
        library_name,
        poster_downloaded,
        poster_skipped,
        fanart_downloaded,
        fanart_skipped,
    )


if __name__ == "__main__":
    main()
