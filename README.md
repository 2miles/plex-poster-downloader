# Plex Poster Downloader

## Acknowledgments

This script is based on a blog post and original script by [Paul Salmon (TechieGuy12)](https://github.com/TechieGuy12):

- Blog post: [Download Movie Posters from a Plex Server](https://www.plexopedia.com/blog/download-movie-posters-from-plex-server/)

Parts of this README and the original script logic were adapted from his work. This version includes additional functionality, refactoring, and expanded documentation.

### Modifications

- Added support for poster handling modes via `--mode`:
  - skip: only download if poster is missing
  - overwrite: always replace existing poster
  - add: save additional posters (e.g. poster-1.jpg, poster-2.jpg)
- Made target Plex library configurable via `--library` argument.
- Introduced .env support for PLEX_URL, PLEX_TOKEN, and path prefix mappings.
- Replaced overly complex filename search (binary + exponential search) with simpler logic.
- Improved error handling for failed API calls and missing environment variables.
- Modernized codebase:
  - Switched from .format() to f-strings
  - Added type hints (Optional, Element, etc.)
- Modularized poster naming, downloading, and path handling
- Improved logging and status messages for better UX.

## Overview

I wanted a better way of [managing my movie posters](https://www.plexopedia.com/plex-media-server/general/posters-artwork/), instead of leaving it to Plex. A way that prevents the posters from being changed by Plex and also allows me to store the actual movie poster file as a `.jpg`

The issue is that posters that are downloaded from Plex or uploaded using the Web app are stored in bundles. These are folders in the [Plex data directory](https://www.plexopedia.com/plex-media-server/general/data-directory/) that contain all the files for the movie.

This script downloads all the movie posters for items currently selected in your Plex library and saves them in their respective movie folder as `poster.jpg`. This ensures you have a local copy of each poster saved in the correct movie folder — one that Plex will detect and use instead of automatically selecting its own.

## Setup

### 1. **Clone this repository**

Open a terminal and run:

```bash
   git clone https://github.com/2miles/plex-posters.git
   cd plex-posters
```

### 2. **Install Dependencies**

Its recomended to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

Or just install manually:

```bash
pip install requests python-dotenv
```

### 3. Get your Plex server URL (PLEX_URL)

This is typically something like: `http://192.168.0.2:32400`

### 4. Get your Plex token (PLEX_TOKEN)

- Log in to your Plex account
- Open Developer Tools (F12) in your browser
- Go to the Network tab
- Play or open a media item
- In the Network tab click on the request
- Click any request to `/library/...`
- In Headers, scroll down to Query String Parameters or Request Headers and look for `X-Plex-Token: abc123xyz456...`

### 5. Create a `.env` file

In the root of the project, create a file called `.env` and add:

```
PLEX_URL=http://192.168.0.2:32400
PLEX_TOKEN=abc123xyz456
CONTAINER_MEDIA_PREFIX=
HOST_MEDIA_PREFIX=
```

### 6. Find and note the library id for each library you want poster downloaded for.

- Open your Plex Web App
- Navigate to a library (e.g. Movies, TV Shows)
- Look at the URL. The ID is the number at the end:
  - `...library?source=1`
  - In this case the library ID = 1

### 7. (Optional) Map Container Paths to NAS Paths

If you’re running Plex in Docker and your media files are stored outside the container, Plex will report file paths like: `/data/media/Movies/Your Movie (2020)`

But the actual path on your NAS might be: `/volume1/data/media/Movies/Your Movie (2020)`

To handle this, set the following variables in your `.env` file:

```
CONTAINER_MEDIA_PREFIX=/data/media
HOST_MEDIA_PREFIX=/volume1/data/media
```

This tells the script to replace /data/media... with /volume1/data/media... so it can find the correct folders when saving posters.

**_If you’re not using Docker, or if Plex’s media paths already match your filesystem, you can leave these variables unset and the script will skip this step automatically._**

## How to use

The script accepts two arguments:

- `--mode`: Controls how posters are handled. Defaults to skip.
  - **skip**: Only download if poster.jpg is missing.
  - **overwrite**: Always replace poster.jpg.
  - **add**: Keep existing posters and save new ones as poster-1.jpg, poster-2.jpg, etc.
- `--library`: The Plex library ID (default: 1). You can find this in the Plex Web App URL.

### Example

- `python3 download_poster.py --mode=skip --library=3`

## Disclaimer

This script interacts directly with your Plex server and filesystem. Use with caution, especially when using `--mode=overwrite` or modifying file permissions. Always make backups before running any automation that alters media files.
