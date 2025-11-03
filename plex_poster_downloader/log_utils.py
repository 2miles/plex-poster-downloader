import os
import re

from colorama import Fore, Style


def log_output_str(filename, title, parent_name, dest_path) -> str:
    """Prints a formatted success message when an image is downloaded."""
    parent_folder = os.path.basename(os.path.dirname(dest_path))
    name, _ = os.path.splitext(filename)

    # Case-insensitive match for folders like "Season 1", "Season 01", etc.
    is_season_folder = re.match(r"(?i)^season\s+\d+$", parent_folder)

    if filename == "fanart.jpg":
        print(
            f"{Fore.LIGHTCYAN_EX}{name}{Style.RESET_ALL}: "
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


def print_summary(args, library_name, library_type, counters):
    """Prints a summary of how many posters/fanart images were downloaded or skipped."""
    if args.poster or args.fanart:
        print(
            f"\n{Style.BRIGHT}Download Summary for Library: {Fore.MAGENTA}{library_name}"
            f"\n{Fore.WHITE}==============================================================="
        )
        if args.poster:
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


def print_no_season_match_warning(show_title, season_title, season_root_path):
    """Warn when no season folder matches."""
    print(
        ###########
        # Use logger for fanart and other warnings, unless --verbose is set
        ###########
        f"{Fore.YELLOW}[WARN]  {Fore.WHITE}No folder matched "
        f"{Style.BRIGHT}{show_title} {Style.RESET_ALL}{season_title} "
        f"-- {Fore.BLUE}{season_root_path}"
    )


def print_no_match_warning(artist_title, album_title, artist_path):
    """Prints warning when no folder matches the album title."""
    print(
        ###########
        # Use logger for fanart and other warnings, unless --verbose is set
        ###########
        f"{Fore.YELLOW}[WARN]  {Fore.WHITE}No folder matched "
        f"{Style.BRIGHT}{artist_title} {Style.RESET_ALL}{album_title} "
        f"-- {Fore.BLUE}{artist_path}"
    )


def maybe_print_rename_message(args, artist_title, album_title, matching_folder):
    if args.rename_albums and not args.force_rename:
        print(
            f"\nMatching album title for {artist_title} - {album_title}"
            f"\n        Plex title:     {Fore.WHITE}{Style.BRIGHT}{album_title}{Style.RESET_ALL}"
            f"\n        Directory name: {matching_folder}"
        )
    if args.rename_albums and args.force_rename:
        print(
            f"Renaming album directory to match Plex album title: "
            f"\n        Plex title:     {Fore.WHITE}{Style.BRIGHT}{album_title}{Style.RESET_ALL}"
            f"\n        Directory name: {matching_folder}"
        )
