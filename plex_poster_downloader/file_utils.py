import difflib
import os
import shutil
from typing import Optional

from colorama import Fore, Style

from .config import CONTAINER_MEDIA_PREFIX, HOST_MEDIA_PREFIX


def resolve_nas_path(container_path: str) -> str:
    """
    Converts a media path from inside the Plex container to the corresponding NAS path.
    Returns the original path if no mapping is configured.
    """
    if (
        CONTAINER_MEDIA_PREFIX
        and HOST_MEDIA_PREFIX
        and container_path.startswith(CONTAINER_MEDIA_PREFIX)
    ):
        return container_path.replace(CONTAINER_MEDIA_PREFIX, HOST_MEDIA_PREFIX, 1)

    return container_path


def resolve_output_path(path: str, mode: str, basename: str = "poster.jpg") -> Optional[str]:
    """Determines the appropriate filename to save an image, based on the specified mode."""
    base_path = os.path.join(path, basename)

    if mode == "overwrite":
        return base_path

    if mode == "skip":
        return base_path if not os.path.exists(base_path) else None

    if mode == "add":
        if not os.path.exists(base_path):
            return base_path

        name, ext = os.path.splitext(basename)
        i = 1

        while True:
            new_path = os.path.join(path, f"{name}-{i}{ext}")
            if not os.path.exists(new_path):
                return new_path
            i += 1

    return None


def list_subfolders(path, quiet: bool = False) -> list[str]:
    """Return a list of subfolders under the given path."""
    try:
        return [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]
    except FileNotFoundError:
        if not quiet:
            print(f"[ERROR] Could not list folders in {path}")
        return []


def find_matching_folder(folders: list[str], possible_names: list[str]) -> Optional[str]:
    """Find a folder whose name matches one of the expected names."""
    return next(
        (f for f in folders if f.lower() in [n.lower() for n in possible_names]),
        None,
    )


def maybe_rename_folder(
    parent_path: str, old_name: str, new_name: str, confirm: bool = False
) -> bool:
    """Optionally rename a folder, prompting the user if confirm=True."""
    old_path = os.path.join(parent_path, old_name)
    new_path = os.path.join(parent_path, new_name)

    # Skip if the folder name is already correct
    if old_name == new_name or not os.path.exists(old_path):
        return False

    if confirm:
        user_input = (
            input(
                f"{Fore.WHITE}Rename album directory to match Plex album title? [y/N]: {Style.RESET_ALL}"
            )
            .strip()
            .lower()
        )
        if user_input != "y":
            print(f"{Fore.YELLOW}Skipped renaming{Style.RESET_ALL}\n")
            return False

    try:
        shutil.move(old_path, new_path)
        print(f"{Fore.GREEN}Renamed successfully{Style.RESET_ALL}\n")
        return True
    except Exception as e:
        print(f"{Fore.RED}Failed to rename: {e}{Style.RESET_ALL}\n")
        return False


def find_best_match(name: str, candidates: list[str]) -> Optional[str]:
    """Return the closest folder match (case-insensitive) using difflib."""
    matches = difflib.get_close_matches(
        name.lower(),
        [c.lower() for c in candidates],
        n=1,
        cutoff=0.6,
    )
    return matches[0] if matches else None
