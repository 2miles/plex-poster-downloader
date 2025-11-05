# Plex Poster Downloader

A Python tool for downloading and organizing artwork from your Plex server.

## Acknowledgments

Originally inspired by a script by [Paul Salmon (TechieGuy12)](https://github.com/TechieGuy12):

- Blog post: [Download Movie Posters from a Plex Server](https://www.plexopedia.com/blog/download-movie-posters-from-plex-server/)

### Notable Features

- Supports posters and fanart for Movies, TV Shows, and Music
- Flexible file handling via `--mode`: `skip`, `overwrite`, or `add`
- Artwork type flags: `--poster` and `--fanart`
- Easily list Plex libraries with `--list-libraries`
- Target Plex librarys via `--library`
- Environment variable support via `.env`:
  - `PLEX_URL`, `PLEX_TOKEN` (required)
  - `CONTAINER_MEDIA_PREFIX`, `HOST_MEDIA_PREFIX` (optional for path mapping)

## Overview

I wanted a better way of [managing my movie posters](https://www.plexopedia.com/plex-media-server/general/posters-artwork/), instead of leaving it to Plex. A way that prevents the posters from being changed by Plex and also allows me to store the actual movie poster file as a `.jpg`

The issue is that posters (and fanart) that are downloaded from Plex or uploaded using the Web app are stored in bundles. These are folders in the [Plex data directory](https://www.plexopedia.com/plex-media-server/general/data-directory/) that contain all the files for the movie, including artwork, but aren’t ideal for manual control, backup, or portability.

This script downloads all the movie, TV show, and music images for items in a given Plex library and saves them in their respective movie folder as `poster.jpg` and `fanart.jpg`. This ensures you have a local copy of each image saved in the correct movie folder — one that Plex will detect and use instead of automatically selecting its own.

You can choose to include specific image types with `--poster` and `--fanart`

## Setup

### 1. **Clone this repository**

Open a terminal and run:

```bash
   git clone https://github.com/2miles/plex-poster-downloader.git
   cd plex-poster-downloader
```

### 2. **Install Dependencies**

It's recomended to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

Or just install manually:

```bash
pip install requests python-dotenv colorama
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

### Arguments

The script accepts several arguments:

- `--mode`: Controls how artwork files are handled. Defaults to `skip`.
  - **skip**: Only download if the file doesn't already exist.
  - **overwrite**: Always replace existing files.
  - **add**: Keep existing files and save new ones as `poster-1.jpg`, `fanart-1.jpg`, etc.
- `--library`: The Plex library ID to download from (default: `1`). (use `--list-libraries` to find your ID's)
- `--poster`: Download `poster.jpg`.
- `--fanart`: Download `fanart.jpg`.
- `--list-libraries`: Print a list of all available Plex libraries (title, type, and ID). Useful for discovering the correct `--library` value before downloading.
- `--rename-albums`: Rename music album directories to match plex metadata (confirm before each rename)
- `--force-rename`: Suppress confirmation for music album renaming.

### How to find your Plex Library ID

Run the script with only the `--list-libraries` before downloading to see all available library names with their corrisponding library ID's:

```bash
python download_posters.py --list-libraries
```

### Examples

#### Download initial posters for movies in library 1 (default library):

- `python3 -m plex_poster_downloader --poster`

#### Add additional poster and fanart images to library 3:

- `python3 -m plex_poster_downloader --mode=add --library=3 --poster --fanart`

#### Overwrite all existing posters and fanart in library 3:

- `python3 -m plex_poster_downloader --mode=overwrite --library=3 --poster --fanart`

### Folder Naming for TV Shows

For TV show and season artwork to save correctly, your TV library should follow the standard Plex folder layout:

```
TV library/
├── Show title/
│   ├── Season 01/
│   ├── ...
│   └── Specials/
└── Another Show title/
```

To correctly download and save season and specials posters, your TV library folders must follow Plex’s standard naming convention.

Valid season folder names include:

```
Season 1
Season 01
1
01
```

The specials folder must be named one of:

```
Specials
Season 0
Season 00
```

These naming patterns are the same ones Plex expects for matching metadata.
If your folder names differ (e.g. S01, Season One), season posters may not download or may be skipped with a warning like:

```
[WARN] Skipping non-standard season title: The Simpsons Season One
```

### Folder Organization for Music

For artist and album artwork to save correctly, your music library should follow the standard Plex folder layout:

```
Music library/
├── Artist Name/
│   ├── Album Title/
│   │   ├── 01 - Track.mp3
│   │   └── ...
│   └── ...
└── Another Artist/
```

## Disclaimer

This script interacts directly with your Plex server and filesystem. Use with caution, especially when using `--mode=overwrite` or modifying file permissions. Always make backups before running any automation that alters media files.
