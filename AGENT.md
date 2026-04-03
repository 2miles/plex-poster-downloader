# AGENT.md

## Purpose

`plex-posters` is a Python CLI for downloading artwork from a Plex server and saving it directly into local media folders as `poster.jpg`, `fanart.jpg`, and `cover.jpg`.

There is no web frontend, backend service, or database. The app runs as a single process and uses:

- Plex's HTTP/XML API as the external data source
- The local filesystem as the persistence layer

## High-Level Architecture

The codebase is organized into a small set of focused modules:

- `plex_poster_downloader/main.py`
  - Entry point and top-level orchestration
  - Validates env config, parses CLI args, selects the correct library handler
- `plex_poster_downloader/args.py`
  - CLI flag definitions
- `plex_poster_downloader/config.py`
  - Loads `.env` values such as `PLEX_URL`, `PLEX_TOKEN`, and optional path mapping prefixes
- `plex_poster_downloader/plex_api.py`
  - Plex API client helpers
  - Fetches library metadata, library contents, and nested metadata for shows and music
- `plex_poster_downloader/library_handlers.py`
  - Main business logic for movie, show, and music libraries
  - Resolves media paths and decides which artwork gets downloaded
- `plex_poster_downloader/artwork.py`
  - Builds artwork URLs and downloads image files
- `plex_poster_downloader/file_utils.py`
  - Path remapping, output filename resolution, folder matching, optional album renaming
- `plex_poster_downloader/log_utils.py`
  - Console output and error logging

## Runtime Model

The normal execution path is:

1. User runs `python -m plex_poster_downloader ...`
2. `main.py` loads config and parses CLI flags
3. The app queries Plex for library metadata and media XML
4. A library-specific handler iterates Plex items
5. The handler resolves the target folder on disk
6. `artwork.py` downloads images into the resolved folder
7. A summary is printed to stdout

## Data Flow

The detailed request-to-filesystem flow is documented in [docs/data-flow.md](/Users/miles/Code/Github/plex-posters/docs/data-flow.md).

Short version:

- Input comes from CLI flags and `.env`
- Metadata comes from Plex API responses
- Paths may be remapped from container paths to host paths
- Images are downloaded and written directly into media directories

## Operational Notes

- The app assumes Plex library folders follow predictable movie, TV, and music layouts
- TV show and music path resolution are derived indirectly from child items such as episodes and tracks
- Album handling may optionally rename folders to match Plex metadata
- File write behavior is controlled by `--mode` with `skip`, `overwrite`, and `add`

## Risks

Structural issues and obvious risks are documented separately in [docs/risks.md](/Users/miles/Code/Github/plex-posters/docs/risks.md).
