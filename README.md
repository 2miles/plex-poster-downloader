# Plex Posters

## Acknowledgments

This script was originally created by [Paul Salmon](https://github.com/TechieGuy12) and can be found at:

[https://www.plexopedia.com/blog/download-movie-posters-from-plex-server/](https://www.plexopedia.com/blog/download-movie-posters-from-plex-server/)

### Modifications

- Added the ability to skip, overwrite, or add a new poster, controlled via command-line arguments.

- Added the ability to choose the target library when running the script.

- Updated the documentation a bit.

## About the script

I wanted a better way of [managing my movie posters](https://www.plexopedia.com/plex-media-server/general/posters-artwork/), instead of leaving it to Plex. A way that prevents the posters from being changed by Plex and also allows me to store the actual movie poster file as a `.jpg`

The issue is that posters that are downloaded from Plex or uploaded using the Web app are stored in bundles. These are folders in the [Plex data directory](https://www.plexopedia.com/plex-media-server/general/data-directory/) that contain all the files for the movie.

This script downloads all the movie posters for items currently selected in your Plex library and saves them in their respective movie folder as `poster.jpg`. This ensures you have a local copy of each poster saved in the correct movie folder — one that Plex will detect and use instead of automatically selecting its own.

## Setup

1. Clone the repo

```
git clone  ...
```

2. Install the dependencies:

```
pip install requests
pip install python-dotenv
```

3. Get your `PLEX_URL`

   - Example: `http://192.168.0.2:32400`

4. Get your `PLEX_TOKEN`

   1. Log in to your Plex account
   2. Open Developer Tools in your browser
   3. Go to the Network tab
   4. In the Web App, browse to any media item (e.g. open a movie or show).
   5. In the Network tab click on the request
   6. In Headers, scroll down to Query String Parameters or Request Headers and look for `X-Plex-Token: abc123xyz456...`

5. Create a `.env` file to store your `PLEX_URL` and `PLEX_TOKEN`

6. Find and note the library id for each library you want poster downloaded for.

   - You can find the ID of the library by going to the library in the Plex web app and looking at the URL. The ID is the number at the end of the URL.
   - Example: `http://192.168.0.2:32400/web/index.html#!/media/da496...a18/com.plexapp.plugins.library?source=1`
     - The ID for this library is 1.

## What does the script do?

The script will make multiple calls to the Plex API to perform the following steps:

- It gets all the movie files by calling the Get All Movies API command. This is done in `get_all_media()`.

- Once all the movies have been retrieved, it will loop through all the movies and then call `get_media_path()` to get the full path of each movie. This path is used to store the downloaded poster.

- Next, `get_poster_url()` function is called to get the URL API command to download the poster. This URL is the Get a Movie's Poster endpoint.

- Once the URL for the poster is known, `download_poster()` downloads and saves it. Then, `next_filename()` determines the appropriate poster filename based on your selected mode.

## How to use it

The script accepts two arguments: **mode** and **library**. If not supplied, the mode defaults to `add` and the library defaults to `1`. **_Be careful with this if you're unsure which library you're targeting._**

### Mode

There are 3 modes in which the script will run:

- **mode=add**
  - On each run adds a new poster `poster-{n+1}.jpg` to the directory
  - If there is no `poster.jpg` in the directory it creates it.
- **mode=skip**
  - Add a `poster.jpg` to the directory if there is not one already, Otherwise skip.
- **mode=overwrite**
  - If a `poster.jpg` exists overwrite it. If not, create one.

### Library

You need to choose a library for the script to run on with the library arg.

### Example

- `python3 download_poster.py --mode=skip --library=3`

## A few notes about the script

Before running the script, there are a few things to keep in mind:

- The script works when it is run from the Plex server since it uses the path of each movie to store the poster.

- If you wish to store the posters in another location, then you can just modify the script to change the location. This will allow the script to be run from another machine.

- Running the script multiple times in `mode=add` will create additional copies of the same poster. This script does not check to see if the poster exists in the folder, it simply adds the poster to the folder, with an incrementing number in the name.
