import os
from dotenv import load_dotenv
import requests
import xml.etree.ElementTree as ET
import shutil

load_dotenv()

plex_url = os.environ.get("PLEX_URL")
plex_token = os.environ.get("PLEX_TOKEN")

# The ID of the library to download posters from.
library = 1

# You can find the ID of the library by going to the library in the Plex web app
# and looking at the URL. The ID is the number at the end of the URL.

# http://192.168.0.2:32400/web/index.html#!/media/da29639fee14f7dbcf83794fdc05dea66ca68a58/com.plexapp.plugins.library?source=1
# Here the ID is 1.

# The IDs of the libraries are as follows:

# 1 - Movies
# 2 - TV Shows
# 3 - Music
# 4 - Animated
# 5 - Documentaries
# 6 - Anime


def get_all_media(id):
    """
    Gets all media for a library.

    Keyword arguments:
    id -- the id of the library
    """
    response = requests.get(
        "{0}/library/sections/{1}/all?X-Plex-Token={2}".format(
            plex_url, library, plex_token
        )
    )
    if response.ok:
        root = ET.fromstring(response.content)
        return root
    else:
        return None


def get_media_path(video_tag):
    """
    Finds the full path to the media item, without the name of the
    media file.

    Keyword arguments:
    video_tag -- the video tag returned by the Plex API
    """
    media_tag = video_tag.find("Media")
    if media_tag is None:
        return None

    part_tag = media_tag.find("Part")
    if part_tag is None:
        return None

    file_path = part_tag.get("file")
    if file_path:
        return next_filename(os.path.dirname(file_path))
    else:
        return None


def get_poster_url(video_tag):
    """
    Gets the URL of the media's poster.

    Keyword arguments:
    video_tag -- the video tag returned by the Plex API
    """
    poster = video_tag.get("thumb")
    if poster:
        return "{0}{1}?X-Plex-Token={2}".format(plex_url, poster, plex_token)
    else:
        return None


def next_filename(path):
    """
    Finds the next free poster name.

    The first poster name is simply poster.jpg, while all subsequent posters
    are in the format: poster-n.jpg, where n is a number.

    e.g. path_pattern = 'poster-%s.txt':

    poster-1.txt
    poster-2.txt
    poster-3.txt

    Keyword arguments:
    path -- the path of the media item
    """
    # Check for the first post file name, and if it doesn't
    # exist then use that
    file_path = "{0}/poster.jpg".format(path)
    if not os.path.exists(file_path):
        return file_path

    # Set the poster naming pattern if at least one poster
    # exists for the media item
    path_pattern = "{0}/poster-%s.jpg".format(path)
    i = 1

    # First do an exponential search
    while os.path.exists(path_pattern % i):
        i = i * 2

    # Result lies somewhere in the interval (i/2..i]
    # We call this interval (a..b] and narrow it down until a + 1 = b
    a, b = (i // 2, i)
    while a + 1 < b:
        c = (a + b) // 2  # interval midpoint
        a, b = (c, b) if os.path.exists(path_pattern % c) else (a, c)

    return path_pattern % b


def download_poster(poster_url, path):
    """
    Downloads the poster from the URL to the specified path.

    Keyword arguments:
    poster_url -- the url of the poster to be downloaded
    path -- the path of the poster
    """
    response = requests.get(poster_url, stream=True)
    if response.status_code == 200:
        with open(path, "wb") as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
    else:
        print("Couldn't download poster. Status code: {0}".format(response.status_code))


root = get_all_media(library)
for video_tag in root.findall("Video"):
    path = get_media_path(video_tag)
    if not path:
        print("The path to the media was not found.")
        continue

    poster_url = get_poster_url(video_tag)
    if poster_url:
        download_poster(poster_url, path)
