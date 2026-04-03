# Plex Poster Downloader

A Python CLI for downloading artwork from a Plex server and saving it directly into your media folders.

It supports:

- movie posters and fanart
- TV show posters, season posters, and fanart
- music artist posters, fanart, and album covers

The goal is to keep artwork as normal image files in your library instead of leaving it buried inside Plex metadata bundles.

## Why This Exists

Plex can manage artwork automatically, but that artwork is often stored in Plex bundle directories rather than alongside your media files. This tool pulls artwork out of Plex and writes it into the media library itself as files such as:

- `poster.jpg`
- `fanart.jpg`
- `cover.jpg`

That gives you more control over backups, portability, and manual artwork management.

It also helps lock in your chosen artwork. If a media folder contains a local `poster.jpg` and Plex is configured to prefer local media assets for that library, Plex will use the local poster instead of replacing it with a different automatically selected one.

## How It Works

The script:

1. connects to your Plex server with `PLEX_URL` and `PLEX_TOKEN`
2. reads metadata from a selected Plex library
3. resolves each media item's folder on disk
4. downloads artwork from Plex
5. writes the image files directly into the media folders

There is no database. The filesystem is the final output.

## Important: Where To Run It

Run this script on a machine that can do both of the following:

- reach your Plex server over the network
- access the actual media folders that will receive `poster.jpg`, `fanart.jpg`, and `cover.jpg`

If you run it on a machine that can talk to Plex but cannot access the library folders, the script will enumerate your library successfully but skip downloads because the output paths do not exist locally.

For many setups, that means running it directly on the NAS, server, or Docker host where the media is mounted.

## Features

- Supports movies, TV shows, and music libraries
- Downloads posters and fanart with `--poster` and `--fanart`
- Lists available Plex libraries with `--list-libraries`
- Supports file handling modes with `--mode`
- Supports container-to-host path remapping for Docker-based Plex installs
- Can optionally rename music album folders to match Plex metadata

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/2miles/plex-poster-downloader.git
cd plex-poster-downloader
```

### 2. Install dependencies

Using a virtual environment is recommended:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Or install the packages directly:

```bash
pip install requests python-dotenv colorama
```

### 3. Get your Plex server URL

Set `PLEX_URL` to your Plex server address, for example:

```text
http://192.168.0.2:32400
```

### 4. Get your Plex token

One easy way:

1. Log in to Plex in a browser
2. Open Developer Tools
3. Open the Network tab
4. Open or play a media item
5. Inspect any request to `/library/...`
6. In Headers, look under Query String Parameters or Request Headers for `X-Plex-Token`

Use that value for `PLEX_TOKEN` in your `.env` file.

### 5. Create a `.env` file

```env
PLEX_URL=http://192.168.0.2:32400
PLEX_TOKEN=abc123xyz456
CONTAINER_MEDIA_PREFIX=
HOST_MEDIA_PREFIX=
```

## Path Mapping For Docker / NAS Setups

If Plex runs in Docker, it may report media paths from inside the container, for example:

```text
/data/media/Movies/Your Movie (2020)
```

But the real path on the machine running this script might be:

```text
/volume1/data/media/Movies/Your Movie (2020)
```

In that case, set:

```env
CONTAINER_MEDIA_PREFIX=/data/media
HOST_MEDIA_PREFIX=/volume1/data/media
```

The script will replace the container prefix with the host prefix before writing files.

Leave these blank if Plex already reports paths that are valid on the machine where you run the script.

## Usage

### Arguments

- `--mode`
  Controls how files are handled. Default: `skip`. Valid values are `skip`, `overwrite`, and `add`.
- `--library`
  Plex library section ID. Default: `1`.
- `--poster`
  Download `poster.jpg`.
- `--fanart`
  Download `fanart.jpg`.
- `--list-libraries`
  Print available Plex libraries and exit.
- `--rename-albums`
  Rename album folders to match Plex metadata, prompting first.
- `--force-rename`
  Rename album folders without prompting.

### File Modes

- `skip`
  Only download artwork when the target file does not already exist.
- `overwrite`
  Replace existing files.
- `add`
  Keep existing files and save additional copies like `poster-1.jpg` or `fanart-1.jpg`.

If your goal is "download only the missing artwork", use `--mode=skip`.

### Find your library IDs

```bash
python -m plex_poster_downloader --list-libraries
```

### Examples

Download only missing posters for the library with ID `1` (the default if `--library` is omitted):

```bash
python3 -m plex_poster_downloader --mode=skip --poster
```

Download only missing posters and fanart for library `3`:

```bash
python3 -m plex_poster_downloader --mode=skip --library=3 --poster --fanart
```

Add extra poster and fanart files without replacing existing ones:

```bash
python3 -m plex_poster_downloader --mode=add --library=3 --poster --fanart
```

Overwrite all existing posters and fanart in library `3`:

```bash
python3 -m plex_poster_downloader --mode=overwrite --library=3 --poster --fanart
```

## Library Layout Expectations

### TV libraries

For show and season artwork to land in the right place, TV folders should follow a standard Plex layout:

```text
TV library/
├── Show Title/
│   ├── Season 01/
│   ├── Season 02/
│   └── Specials/
└── Another Show/
```

Recognized season folder names include:

- `Season 1`
- `Season 01`
- `1`
- `01`

Recognized specials folder names include:

- `Specials`
- `Season 0`
- `Season 00`

If your folders use non-standard names such as `S01` or `Season One`, season posters may be skipped.

### Music libraries

For artist, album, and cover artwork to resolve correctly, music libraries should look roughly like this:

```text
Music library/
├── Artist Name/
│   ├── Album Title/
│   │   ├── 01 - Track.mp3
│   │   └── ...
│   └── ...
└── Another Artist/
```

## Troubleshooting

### The script lists my library but downloads nothing

Check that you are running the script on a machine that can access the media folders locally.

Common causes:

- running the script on a laptop instead of the NAS/server
- stale `CONTAINER_MEDIA_PREFIX` / `HOST_MEDIA_PREFIX` values
- media paths reported by Plex do not match the local filesystem on that machine

### I only want missing artwork, not extra numbered files

Use:

```bash
--mode=skip
```

`--mode=add` is for keeping the current file and adding another one such as `poster-1.jpg`.

### Every download fails

Check:

- `PLEX_URL`
- `PLEX_TOKEN`
- whether the resolved media path exists on disk
- whether the user running the script can write into the media folders

## Disclaimer

This script talks directly to your Plex server and writes directly into your media library. Use caution, especially with `--mode=overwrite` or folder renaming. Back up important media metadata before running automation against large libraries.

## Acknowledgments

Originally inspired by work from [Paul Salmon (TechieGuy12)](https://github.com/TechieGuy12):

- [Download Movie Posters from a Plex Server](https://www.plexopedia.com/blog/download-movie-posters-from-plex-server/)
