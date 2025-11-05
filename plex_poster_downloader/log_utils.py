import os
import re

from colorama import Fore, Style


def log_warning(message):
    """Log a non-fatal warning in yellow."""
    print(f"{Fore.YELLOW}[WARN]{Fore.WHITE} {message}")


def log_fatal_error(message):
    """Log a fatal error in red and exit immediately."""
    print(f"{Fore.RED}[ERROR]{Fore.WHITE} {message}")
    exit(1)


def bright_text(text):
    """Returns the text formatted in bright style."""
    return f"{Style.BRIGHT}{Fore.WHITE}{text}{Style.RESET_ALL}"


def bright_magenta_text(text):
    """Returns the text formatted in bright style."""
    return f"{Style.BRIGHT}{Fore.MAGENTA}{text}{Style.RESET_ALL}"


def bright_yellow_text(text):
    """Returns the text formatted in bright style."""
    return f"{Style.BRIGHT}{Fore.YELLOW}{text}{Style.RESET_ALL}"


def yellow_text(text):
    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"


def green_text(text):
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}"


def red_text(text):
    return f"{Fore.RED}{text}{Style.RESET_ALL}"


def light_cyan_text(text):
    return f"{Fore.LIGHTCYAN_EX}{text}{Style.RESET_ALL}"


def cyan_text(text):
    return f"{Fore.CYAN}{text}{Style.RESET_ALL}"


def magenta_text(text):
    return f"{Fore.MAGENTA}{text}{Style.RESET_ALL}"


def blue_text(text):
    return f"{Fore.BLUE}{text}{Style.RESET_ALL}"


def log_output_str(filename: str, title: str, parent_name: str, dest_path: str) -> None:
    """Print a formatted success message when an image is downloaded."""
    parent_folder = os.path.basename(os.path.dirname(dest_path))
    name, _ = os.path.splitext(filename)

    is_season_folder = bool(re.match(r"(?i)^season\s+\d+$", parent_folder))
    is_special = title.lower().startswith("specials")

    if filename == "fanart.jpg":
        print(f"{light_cyan_text(name)}: {bright_text(title)}")
        return

    if filename == "cover.jpg":
        print(f"{cyan_text(name)}: {bright_text(parent_name)} → {title}")
        return

    if filename == "poster.jpg":
        if is_season_folder or is_special:
            print(f"{cyan_text(name)}: {bright_text(parent_name)} → {title}")
        else:
            print(f"{cyan_text(name)}: {bright_text(title)}")


def log_summary(args, library_name, library_type, counters):
    """Prints a summary of how many posters/fanart images were downloaded or skipped."""
    if not (args.poster or args.fanart):
        return

    print(
        f"\n{bright_text('Download Summary for Library:')} {magenta_text(library_name)}"
        f"\n==============================================================="
    )

    def print_stat(label, key):
        downloaded = counters[key]["downloaded"]
        skipped = counters[key]["skipped"]

        print(f"{label} downloaded: {bright_text(downloaded)}")
        if args.mode == "skip":
            print(f"{label} skipped: {bright_text(skipped)}")

    if args.poster:
        print_stat("Posters", "poster")
    if args.fanart:
        print_stat("Fanart", "fanart")
    if library_type == "artist":
        print_stat("Covers", "cover")

    print("\n\n")


def log_no_folder_match(parent_name: str, child_name: str, path: str, context: str = None):
    """
    Warn when no folder matches an expected subdirectory (season, album, etc.).

    Args:
        parent_name: The main entity (e.g., show or artist name)
        child_name: The sub-entity (e.g., season or album title)
        path: The parent folder path
        context: Optional context string (e.g. 'season', 'album') for clarity
    """
    context_str = f" ({context})" if context else ""
    log_warning(
        f"No folder matched{context_str} {bright_text(parent_name)} {child_name} -- {blue_text(path)}"
    )


def log_rename_prompt(artist_title, album_title, matching_folder, force):
    if not force:
        print(
            f"\nMatching album title for {artist_title} - {album_title}"
            f"\n        Plex title:     {bright_text(album_title)}"
            f"\n        Directory name: {bright_yellow_text(matching_folder)}"
        )
    else:
        print(
            f"Renaming album directory to match Plex album title: "
            f"\n        Plex title:     {bright_text(album_title)}"
            f"\n        Directory name: {bright_yellow_text(matching_folder)}"
        )


def log_no_album_cover(album_title, artist_title):
    log_warning(f"No cover found for '{album_title}' ({artist_title})")


def log_invalid_cover_url(album_title, artist_title):
    log_warning(f"Invalid cover URL for '{album_title}' ({artist_title})")


def log_nonstandard_season_title(season_title):
    log_warning(f"Skipping non-standard season title: {Style.BRIGHT}{season_title}")


def log_missing_artwork(kind: str, title: str):
    """Logs a warning for missing poster, fanart, or other artwork."""
    log_warning(f"No {kind} found for '{title}'")


def log_missing_media_path(title=None, library_type=None):
    """Warn when the Plex XML doesn’t include a usable file path."""
    if title and library_type:
        log_warning(f"Could not resolve path for {library_type}: '{title}'")
    elif title:
        log_warning(f"Could not resolve path for '{title}'")
    else:
        log_warning("Could not resolve media path")


def log_missing_art_url(kind, title):
    log_warning(f"No {kind} URL found for '{title}'")


def log_failed_image_download(kind, title):
    log_warning(f"Failed to download {kind} for '{title}'")


def log_failed_folder_listing(path):
    log_warning(f"Could not list folders in {blue_text(path)}")


def log_plex_connection_error(status_code, plex_url):
    log_fatal_error(
        f"Could not connect to Plex at {blue_text(plex_url)} (HTTP {status_code}). "
        "Verify PLEX_URL and PLEX_TOKEN in your .env file."
    )


def log_available_libraries(libraries: list[tuple[int, str, str]]):
    """Print a formatted list of available Plex libraries."""
    print(
        f"\n\n{bright_text('Available Plex Libraries:')}"
        f"\n{bright_text('===============================================================')}"
    )

    for lib_id, title, lib_type in libraries:
        print(
            f"{bright_magenta_text(title):<40}"
            f"type: {yellow_text(lib_type):<20}"
            f"library: {bright_text(lib_id)}"
        )
    print("\n")
