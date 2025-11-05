import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="""
    Download poster.jpg and/or fanart.jpg for media items from a Plex library.

    Supports configurable overwrite modes, per-artwork-type toggling, and results summary.

    Use --list-libraries to view available libraries before downloading.

    Examples:
    python download_posters.py --list-libraries
    python download_posters.py --poster --fanart
    python download_posters.py --library 3 --poster
    python download_posters.py --library 4 --mode overwrite --fanart
    python download_posters.py --library 2 --mode add --poster --fanart
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
        "--poster",
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
        "--rename-albums",
        action="store_true",
        default=False,
        help="Rename album folders to match Plex titles (prompts before renaming by default).",
    )

    parser.add_argument(
        "--force-rename",
        action="store_true",
        default=False,
        help="Rename album folders without prompting for confirmation (use with caution).",
    )

    return parser.parse_args()
