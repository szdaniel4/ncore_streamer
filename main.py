import argparse
import getpass
import os
import sys
import termios
import tty

from ncore.client import NcoreClient, NcoreLoginError
from ncore.config import PASSWORD as CONFIG_PASSWORD
from ncore.config import PEERFLIX_DOWNLOAD_DIR
from ncore.config import PEERFLIX_VLC
from ncore.config import TORRENT_DOWNLOAD_DIR
from ncore.config import USERNAME as CONFIG_USERNAME
from ncore.models import Torrent
from ncore.search import NcoreSearch
from peerflix.peerflix import stream


def _configured_value(value: str, placeholder: str) -> str | None:
    if not value or value == placeholder:
        return None

    return value


def resolve_credentials(username: str | None) -> tuple[str, str]:
    resolved_username = username or _configured_value(
        CONFIG_USERNAME,
        "my_username_here",
    )

    if not resolved_username:
        resolved_username = input("nCore username: ")

    resolved_password = _configured_value(
        CONFIG_PASSWORD,
        "my_password_here",
    )

    if not resolved_password:
        resolved_password = getpass.getpass("nCore password: ")

    return resolved_username, resolved_password


def create_client(username: str, password: str) -> NcoreClient:

    client = NcoreClient(
        username=username,
        password=password,
    )

    try:
        client.login()

    except NcoreLoginError:
        raise

    except Exception as e:
        raise RuntimeError(f"Error: {e}")

    return client


def login_command(username: str | None):
    resolved_username, resolved_password = resolve_credentials(username)
    create_client(resolved_username, resolved_password)

    print("Successful login.")


def prompt_query(initial_query: str | None) -> str:
    if initial_query:
        return initial_query

    return input("What to search for: ").strip()


def _read_key() -> str:
    if not sys.stdin.isatty():
        raise RuntimeError("terminal is necessary for key reading")

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        first = sys.stdin.read(1)

        if first == "\x1b":
            second = sys.stdin.read(1)
            third = sys.stdin.read(1)
            return first + second + third

        return first

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _render_torrents(torrents: list[Torrent], selected_index: int):
    os.system("clear")
    print("Results. Up/down: navigate, Enter: select")
    print("=" * 80)

    for index, torrent in enumerate(torrents):
        prefix = "\t> " if index == selected_index else "\t  "
        lines = str(torrent).splitlines()

        if not lines:
            continue

        print(f"{prefix}{lines[0]}")

        for line in lines[1:]:
            print(f"\t  {line}")

        print()


def choose_torrent(torrents: list[Torrent]) -> Torrent | None:
    selected_index = 0

    while True:
        _render_torrents(torrents, selected_index)
        key = _read_key()

        if key == "\x1b[A":
            selected_index = (selected_index - 1) % len(torrents)
        elif key == "\x1b[B":
            selected_index = (selected_index + 1) % len(torrents)
        elif key in {"\r", "\n"}:
            return torrents[selected_index]
        elif key == "q":
            return None


def search_command(username: str | None, query: str | None):
    resolved_username, resolved_password = resolve_credentials(username)
    client = create_client(resolved_username, resolved_password)

    print("Successful login.")
    search = NcoreSearch(client)

    while True:
        query = prompt_query(query)

        if not query:
            print("Empty search query.")
            query = None
            continue

        print(f"Kereses: {query}")
        print()

        try:
            torrents = search.search(query)
        except Exception as e:
            print(f"Search error: {e}")
            query = None
            continue

        if not torrents:
            print("No results.")
            query = None
            continue

        selected = choose_torrent(torrents)

        if selected is None:
            query = None
            continue

        print()
        print(f"Selected: {selected.name}")

        try:
            saved_path = client.download_torrent(
                selected.id,
                TORRENT_DOWNLOAD_DIR,
                suggested_name=selected.name,
            )
        except Exception as e:
            print(f"Torrent download error: {e}")
            return

        print(f"Saved torrent: {saved_path}")

        return saved_path


def main():
    parser = argparse.ArgumentParser(
        description="nCore CLI"
    )

    parser.add_argument(
        "command",
        nargs="?",
        choices=[
            "login",
            "search",
        ],
        default="search",
        help="Command to execute",
    )

    parser.add_argument(
        "query",
        nargs="?",
        help="Search query",
    )

    parser.add_argument(
        "-u",
        "--username",
        help="nCore username (optional, can be set in config.py)",
    )

    args = parser.parse_args()

    try:
        if args.command == "login":
            login_command(args.username)

        elif args.command == "search":
            search_path = search_command(
                args.username,
                args.query,
            )

            if search_path:
                stream(search_path, vlc=PEERFLIX_VLC, download_path=PEERFLIX_DOWNLOAD_DIR)

    except NcoreLoginError as e:
        print(f"Login error: {e}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()