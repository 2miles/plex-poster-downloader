# Plex Poster Downloader

## Acknowledgments

This script is based on a blog post and original script by [Paul Salmon (TechieGuy12)](https://github.com/TechieGuy12):

- Blog post: [Download Movie Posters from a Plex Server](https://www.plexopedia.com/blog/download-movie-posters-from-plex-server/)

Parts of the logic and some wording were adapted from his work. This version has been significantly expanded and refactored for additional flexibility and clarity.

### Notable Features & Enhancements

- Supports both `poster.jpg` and `fanart.jpg` downloads
- Poster handling modes via `--mode`: `skip`, `overwrite`, or `add`
- Image type inclusion flags: `--posters` and `--fanart`
- Configurable Plex library via `--library`
- Environment variable support via `.env`:
  - `PLEX_URL`, `PLEX_TOKEN`
  - `CONTAINER_MEDIA_PREFIX`, `HOST_MEDIA_PREFIX` (optional path mapping)
- Clean, modular code with helpful output and error handling

## Overview

I wanted a better way of [managing my movie posters](https://www.plexopedia.com/plex-media-server/general/posters-artwork/), instead of leaving it to Plex. A way that prevents the posters from being changed by Plex and also allows me to store the actual movie poster file as a `.jpg`

The issue is that posters (and fanart) that are downloaded from Plex or uploaded using the Web app are stored in bundles. These are folders in the [Plex data directory](https://www.plexopedia.com/plex-media-server/general/data-directory/) that contain all the files for the movie, including artwork, but aren’t ideal for manual control, backup, or portability.

This script downloads all the movie posters and fanart images for items currently selected in your Plex library and saves them in their respective movie folder as `poster.jpg` and `fanart.jpg`. This ensures you have a local copy of each image saved in the correct movie folder — one that Plex will detect and use instead of automatically selecting its own.

You can choose to include specific image types with `--posters` and `--fanart`

## Setup

### 1. **Clone this repository**

Open a terminal and run:

```bash
   git clone https://github.com/2miles/plex-posters.git
   cd plex-posters
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

### 6. Find and note the library id for each library you want postes downloaded from.

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

### Arguments

The script accepts several arguments:

- `--mode`: Controls how artwork files are handled. Defaults to `skip`.
  - **skip**: Only download if the file doesn't already exist.
  - **overwrite**: Always replace existing files.
  - **add**: Keep existing files and save new ones as `poster-1.jpg`, `fanart-1.jpg`, etc.
- `--library`: The Plex library ID to download from (default: `1`). You can find this in the Plex Web App URL.
- `--posters`: Download `poster.jpg`.
- `--fanart`: Download `fanart.jpg`.

### Examples

> 📝 Replace `--library=3` with the actual ID of the Plex library you want to target.
>
> You can find this by opening the Plex Web App and selecting a library — the number at the end of the URL is the library ID.
>
> Example: `http://localhost:32400/web/index.html#!/library/sections/3` → Library ID = `3`
>
> If you only have one library, it's usually Movies (`--library=1`), and you can omit the `--library` argument entirely.

#### Download posters for movies you don't yethave a `poster.jpg` for:

- `python3 download_posters.py --library=3 --posters`

#### Add additional poster and fanart images without overwriting existing ones:

- `python3 download_posters.py --mode=add --library=3 --posters --fanart`

#### Overwrite all existing posters and fanart:

- `python3 download_posters.py --mode=overwrite --library=3 --posters --fanart`

## Disclaimer

This script interacts directly with your Plex server and filesystem. Use with caution, especially when using `--mode=overwrite` or modifying file permissions. Always make backups before running any automation that alters media files.
