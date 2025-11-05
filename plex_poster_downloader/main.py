from .args import parse_args
from .config import check_required_env
from .library_handlers import handle_movie_library, handle_show_library, handle_music_library
from .log_utils import log_summary, log_fatal_error
from .plex_api import get_library_metadata, list_plex_libraries, get_all_media

"""
This script is adapted from an original version by Paul Salmon (TechieGuy12),
available via https://www.plexopedia.com/blog/download-movie-posters-from-plex-server/

Significant modifications and enhancements were made to support poster naming modes,
environment-based configuration, error handling, and improved documentation.
"""


def main_logic(args):
    library = get_library_metadata(args.library)
    if not library:
        log_fatal_error(f"Failed to retrieve metadata for library ID {args.library}")

    library_name = library["title"]
    library_type = library["type"]

    root = get_all_media(args.library)
    if root is None:
        log_fatal_error(f"Failed to retrieve media for library ID {args.library}")

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

    log_summary(args, library_name, library_type, counters)


def main():
    check_required_env()
    args = parse_args()

    if args.list_libraries:
        list_plex_libraries()
        return

    if args.force_rename:
        args.rename_albums = True

    main_logic(args)


if __name__ == "__main__":
    main()
