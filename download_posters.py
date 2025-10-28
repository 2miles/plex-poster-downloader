"""
This script is adapted from an original version by Paul Salmon (TechieGuy12),
available via https://www.plexopedia.com/blog/download-movie-posters-from-plex-server/

Significant modifications and enhancements were made to support poster naming modes,
environment-based configuration, error handling, and improved documentation.
"""

import argparse
import difflib
from dotenv import load_dotenv
import os
import re
import requests
import shutil
from typing import Literal, Optional
import xml.etree.ElementTree as ET

try:
    from colorama import Fore, Style, init

    init(autoreset=True)
except ImportError:

    class Dummy:
        def __getattr__(self, _):
            return ""

    Fore = Style = Dummy()


load_dotenv()

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
CONTAINER_MEDIA_PREFIX = os.getenv("CONTAINER_MEDIA_PREFIX", "")
HOST_MEDIA_PREFIX = os.getenv("HOST_MEDIA_PREFIX", "")


# === Environment & Argument Handling =================================


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


def parse_args():
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

    parser.add_argument(
        "--auto-rename",
        action="store_true",
        default=False,
        help="Automatically rename mismatched album folders to match Plex metadata (use with caution).",
    )

    parser.add_argument(
        "--confirm-rename",
        action="store_true",
        default=False,
        help="Ask for confirmation before renaming each folder (requires --auto-rename).",
    )

    return parser.parse_args()


# === Main Orchestration ===============================================


def main_download_logic(args):
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

    counters = {
        "poster": {"downloaded": 0, "skipped": 0},
        "fanart": {"downloaded": 0, "skipped": 0},
        "cover": {"downloaded": 0, "skipped": 0},
    }

    if library_type == "movie":
        handle_movie_library(root, args, counters)
    elif library_type == "show":
        handle_show_library(root, args, counters)
    elif library_type == "artist":
        handle_music_library(root, args, counters)
    else:
        print(f"Unsupported library type: {library_type}")

    print_summary(args, library_name, library_type, counters)


def print_summary(args, library_name, library_type, counters):
    """Prints a summary of how many posters/fanart images were downloaded or skipped."""
    if args.posters or args.fanart:
        print(
            f"\n{Style.BRIGHT}Download Summary for Library: {Fore.MAGENTA}{library_name}"
            f"\n{Fore.WHITE}==============================================================="
        )
        if args.posters:
            print(f"Posters downloaded: {Style.BRIGHT}{counters['poster']['downloaded']}")
            if args.mode == "skip":
                print(f"Posters skipped: {Style.BRIGHT}{counters['poster']['skipped']}")
        if args.fanart:
            print(f"Fanart downloaded: {Style.BRIGHT}{counters['fanart']['downloaded']}")
            if args.mode == "skip":
                print(f"Fanart skipped: {Style.BRIGHT}{counters['fanart']['skipped']}")
        if library_type == "artist":
            print(f"Covers downloaded: {Style.BRIGHT}{counters['cover']['downloaded']}")
            if args.mode == "skip":
                print(f"Covers skipped: {Style.BRIGHT}{counters['cover']['skipped']}")
        print("\n\n")


# === Library Handling ================================================


def sanitize_filename(name: str) -> str:
    """Removes or replaces characters that are invalid or problematic in file or folder names."""
    # Replace forbidden characters for all major OSes
    sanitized = re.sub(r'[\\/*?:"<>|]', "", name)
    # Remove periods, except when used before file extensions
    sanitized = sanitized.replace(".", "")
    # Trim whitespace and trailing dots/spaces
    sanitized = sanitized.strip().strip(".")
    return sanitized


def maybe_rename_folder(
    parent_path: str, old_name: str, new_name: str, confirm: bool = False
) -> bool:
    """Optionally rename a folder, prompting the user if confirm=True."""
    old_path = os.path.join(parent_path, old_name)
    new_path = os.path.join(parent_path, new_name)

    # Skip if the folder name is already correct
    if old_name == new_name or not os.path.exists(old_path):
        return False

    if confirm:
        user_input = (
            input(
                f"{Fore.WHITE}Rename album directory to match Plex album title? [y/N]: {Style.RESET_ALL}"
            )
            .strip()
            .lower()
        )
        if user_input != "y":
            print(f"Skipped renaming\n")
            return False

    try:
        shutil.move(old_path, new_path)
        print(f"{Fore.GREEN}Renamed successfully{Style.RESET_ALL}\n")
        return True
    except Exception as e:
        print(f"{Fore.RED}Failed to rename: {e}{Style.RESET_ALL}\n")
        return False


def handle_movie_library(root, args, counters):
    for video_tag in root.findall("Video"):
        media_path = get_media_path(video_tag)
        if not media_path:
            print("The path to the media was not found.")
            continue
        media_path = resolve_nas_path(media_path)
        download_artwork(video_tag, media_path, args, counters)


def handle_show_library(root, args, counters):
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
        download_artwork(video_tag, media_path, args, counters)

        # 3. Season-level poster download
        season_resp = get_plex_response(f"/library/metadata/{rating_key}/children")
        if not season_resp.ok:
            continue
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

            if season_title.lower() in ["specials", "season 0", "season 00"]:
                possible_names = ["Specials", "Season 00", "Season 0"]
            else:
                # handle "Season X" style titles
                match = re.match(r"Season\s+(\d+)", season_title, re.IGNORECASE)
                if not match:
                    if season_title.lower() == "all episodes":
                        continue
                    print(
                        f"{Fore.YELLOW}[WARN]  {Fore.WHITE}Skipping non-standard season title: "
                        f"{Style.BRIGHT}{show_title} {Style.RESET_ALL}{season_title} -- {Fore.BLUE}{season_root_path}"
                    )
                    continue

                season_num = int(match.group(1))
                possible_names = [f"Season {season_num}", f"Season {season_num:02d}"]

            matching_folder = next(
                (f for f in folders if f.lower() in [name.lower() for name in possible_names]),
                None,
            )

            if not matching_folder:
                print(
                    f"{Fore.YELLOW}[WARN]  {Fore.WHITE}No folder matched "
                    f"{Style.BRIGHT}{show_title} {Style.RESET_ALL}{season_title} -- {Fore.BLUE}{season_root_path}"
                )
                continue

            season_path = os.path.join(season_root_path, matching_folder)

            if args.posters:
                result = handle_artwork_download("poster", season, season_path, args.mode)
                increment_counter(result, counters["poster"])


def handle_music_library(root, args, counters):
    """Handles downloading artist and album artwork for a Plex music library."""

    for artist_tag in root.findall("Directory"):
        artist_title = artist_tag.get("title", "Unknown Artist")
        artist_key = artist_tag.get("ratingKey")
        if not artist_key:
            continue

        # Resolve path based on first album/track
        artist_path = get_path_from_first_album(artist_key)
        if not artist_path:
            print(f"Could not resolve path for artist: {artist_title}")
            continue

        artist_path = resolve_nas_path(os.path.dirname(artist_path))

        # --- Artist-level artwork ---
        if args.posters:
            thumb = artist_tag.get("thumb")
            if thumb:
                result = handle_artwork_download("poster", artist_tag, artist_path, args.mode)
                increment_counter(result, counters["poster"])
            else:
                print(f"{Fore.YELLOW}[WARN]  {Fore.WHITE}No poster found for '{artist_title}'")

        if args.fanart:
            art = artist_tag.get("art")
            if art:
                result = handle_artwork_download("fanart", artist_tag, artist_path, args.mode)
                increment_counter(result, counters["fanart"])
            else:
                print(f"{Fore.YELLOW}[WARN]  {Fore.WHITE}No fanart found for '{artist_title}'")

        # --- Album-level artwork ---
        if not args.posters:
            continue  # only download album covers if --posters is active

        album_resp = get_plex_response(f"/library/metadata/{artist_key}/children")
        if not album_resp.ok:
            continue

        album_root = ET.fromstring(album_resp.content)

        for album_tag in album_root.findall("Directory"):
            album_title = album_tag.get("title")
            album_thumb = album_tag.get("thumb")

            if not album_thumb:
                print(
                    f"{Fore.YELLOW}[WARN]  {Fore.WHITE}No cover found for "
                    f"'{album_title}' ({artist_title})"
                )
                continue

            sanitized_title = sanitize_filename(album_title)
            album_path = os.path.join(artist_path, sanitized_title)

            # --- Folder matching logic (fuzzy match + optional rename) ---
            if not os.path.isdir(album_path):
                try:
                    existing_folders = [
                        f
                        for f in os.listdir(artist_path)
                        if os.path.isdir(os.path.join(artist_path, f))
                    ]
                except FileNotFoundError:
                    existing_folders = []

                matches = difflib.get_close_matches(
                    sanitized_title.lower(),
                    [f.lower() for f in existing_folders],
                    n=1,
                    cutoff=0.6,
                )

                if matches:
                    matching_folder = next(f for f in existing_folders if f.lower() == matches[0])
                    album_path = os.path.join(artist_path, matching_folder)

                    if args.auto_rename and args.confirm_rename:
                        print(
                            f"\nMatching album title for {artist_title} - {album_title}"
                            f"\n        Plex title:     {Fore.WHITE}{Style.BRIGHT}{album_title}{Style.RESET_ALL}"
                            f"\n        Directory name: {matching_folder}"
                        )
                    elif args.auto_rename:
                        print(
                            f"Renaming album directory to match Plex album title: "
                            f"\n        Plex title:     {Fore.WHITE}{Style.BRIGHT}{album_title}{Style.RESET_ALL}"
                            f"\n        Directory name: {matching_folder}"
                        )

                    renamed = False
                    sanitized_title = sanitize_filename(album_title)

                    # --- Auto-rename (optional) ---
                    if args.auto_rename and matching_folder != sanitized_title:
                        renamed = maybe_rename_folder(
                            artist_path,
                            matching_folder,
                            sanitized_title,
                            confirm=args.confirm_rename,
                        )

                        # update paths if rename succeeded
                        if renamed:
                            matching_folder = sanitized_title
                            album_path = os.path.join(artist_path, matching_folder)

                # proceed with cover download using the correct folder
                else:
                    print(
                        f"{Fore.YELLOW}[WARN]  {Fore.WHITE}No folder matched "
                        f"{Style.BRIGHT}{artist_title} {Style.RESET_ALL}{album_title} "
                        f"-- {Fore.BLUE}{artist_path}"
                    )
                    continue

            # --- Download cover image ---
            dest_path = resolve_output_path(album_path, args.mode, "cover.jpg")
            if not dest_path:
                increment_counter("skipped", counters["cover"])
                continue

            url = f"{PLEX_URL}{album_thumb}?X-Plex-Token={PLEX_TOKEN}"
            if not album_thumb or "None" in url:
                print(
                    f"{Fore.YELLOW}[WARN]{Fore.WHITE} Invalid cover URL for album "
                    f"'{album_title}' ({artist_title})"
                )
                continue

            download_image(url, dest_path)
            log_output_str("cover.jpg", album_title, artist_title, dest_path)
            increment_counter("downloaded", counters["cover"])


# === Plex API Integration ===============================================


def get_plex_response(endpoint: str, params: dict = None) -> requests.Response:
    """GET wrapper for Plex API with token injection"""
    url = f"{PLEX_URL}{endpoint}"
    if params is None:
        params = {}
    params["X-Plex-Token"] = PLEX_TOKEN

    response = requests.get(url, params=params)
    return response


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


def get_all_media(id: int) -> Optional[ET.Element]:
    """Fetch all media items from a Plex library section by ID."""
    response = requests.get(f"{PLEX_URL}/library/sections/{id}/all?X-Plex-Token={PLEX_TOKEN}")
    if not response.ok:
        return None
    return ET.fromstring(response.content)


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


def list_plex_libraries():
    """Prints a formatted list of Plex libraries (title, type, and ID), sorted by ID."""
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


# === Path & File Resolution ==============================================


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
    """
    Converts a media path from inside the Plex container to the corresponding NAS path.
    Returns the original path if no mapping is configured.
    """
    if (
        CONTAINER_MEDIA_PREFIX
        and HOST_MEDIA_PREFIX
        and container_path.startswith(CONTAINER_MEDIA_PREFIX)
    ):
        return container_path.replace(CONTAINER_MEDIA_PREFIX, HOST_MEDIA_PREFIX, 1)

    return container_path


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


# === Artwork Logic ==============================================


def get_image_url(image_type: str, video_tag: ET.Element) -> Optional[str]:
    """Constructs the full URL to download the fanart or poster for a media item."""
    if image_type == "poster":
        image = video_tag.get("thumb")
    elif image_type == "fanart":
        image = video_tag.get("art")
    else:
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

    if not url:
        print(f"[WARN] No {kind} URL found for '{title}'")
        return "none"

    if not dest_path:
        return "skipped"

    download_image(url, dest_path)
    log_output_str(filename, title, show_name, dest_path)
    return "downloaded"


def download_artwork(tag, path, args, counters):
    if args.posters:
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


def increment_counter(result, counters):
    if result == "skipped":
        counters["skipped"] += 1
    elif result == "downloaded":
        counters["downloaded"] += 1


def log_output_str(filename, title, parent_name, dest_path) -> str:
    """Prints a formatted success message when an image is downloaded."""
    parent_folder = os.path.basename(os.path.dirname(dest_path))
    name, _ = os.path.splitext(filename)

    # Case-insensitive match for folders like "Season 1", "Season 01", etc.
    is_season_folder = re.match(r"(?i)^season\s+\d+$", parent_folder)

    if filename == "fanart.jpg":
        print(
            f"{Fore.LIGHTCYAN_EX}{name} {Style.RESET_ALL}: "
            f"{Style.BRIGHT}{Fore.WHITE}{title}{Style.RESET_ALL}"
        )
    elif filename == "poster.jpg":
        location_type = "season" if is_season_folder else "show"
        if location_type == "show" and not title.lower().startswith("specials"):
            print(
                f"{Fore.CYAN}{name}{Style.RESET_ALL}: "
                f"{Style.BRIGHT}{Fore.WHITE}{title}{Style.RESET_ALL}"
            )
        if location_type == "season" or (
            location_type == "show" and title.lower().startswith("specials")
        ):
            print(
                f"{Fore.CYAN}{name}{Style.RESET_ALL}: "
                f"{Fore.WHITE}{Style.BRIGHT}{parent_name} {Style.RESET_ALL}→ {title}"
            )
    elif filename == "cover.jpg":
        print(
            f"{Fore.CYAN}{name} {Style.RESET_ALL}: "
            f"{Fore.WHITE}{Style.BRIGHT}{parent_name} {Style.RESET_ALL}→ {title}"
        )


# === Entry Point =========================================================


def main():
    check_required_env()
    args = parse_args()

    if args.list_libraries:
        list_plex_libraries()
        return

    main_download_logic(args)


if __name__ == "__main__":
    main()
