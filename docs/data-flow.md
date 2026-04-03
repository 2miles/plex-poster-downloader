1. User runs the CLI with flags like --library, --poster, --fanart, --mode.
2. The app loads .env, validates PLEX_URL and PLEX_TOKEN, and fetches Plex library metadata plus section contents in plex_poster_downloader/
   main.py:16 and plex_poster_downloader/plex_api.py:31.
3. The appropriate handler iterates Plex XML nodes:
   - Movies: extract media folder directly from each Video in plex_poster_downloader/library_handlers.py:36
   - Shows: resolve the show folder indirectly via first season/episode, then fetch season metadata in plex_poster_downloader/
     library_handlers.py:47
   - Music: resolve artist path via first album/track, then optionally fuzzy-match/rename album folders in plex_poster_downloader/
     library_handlers.py:129
4. Paths are optionally remapped from container paths to host paths via env prefixes in plex_poster_downloader/file_utils.py:10.
5. Artwork URLs are built from Plex metadata and downloaded with requests; output filenames are chosen based on skip / overwrite / add mode in
   plex_poster_downloader/artwork.py:14 and plex_poster_downloader/file_utils.py:25.
6. Images are written straight to disk. That filesystem is effectively the “database”.
