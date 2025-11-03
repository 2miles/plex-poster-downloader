import os
from dotenv import load_dotenv

try:
    from colorama import Fore, Style, init

    init(autoreset=True)
except ImportError:

    class Dummy:
        def __getattr__(self, _):
            return ""

    Fore = Style = Dummy()

load_dotenv()

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
CONTAINER_MEDIA_PREFIX = os.getenv("CONTAINER_MEDIA_PREFIX", "")
HOST_MEDIA_PREFIX = os.getenv("HOST_MEDIA_PREFIX", "")


def check_required_env():
    """
    Checks that all required environment variables are set, and exits with an error if any are
    missing.
    """
    missing = []
    if not PLEX_URL:
        missing.append("PLEX_URL")
    if not PLEX_TOKEN:
        missing.append("PLEX_TOKEN")
    if missing:
        print(f"Error: Missing environment variable(s): {', '.join(missing)}")
        print("Please set them in your .env file.")
        exit(1)
