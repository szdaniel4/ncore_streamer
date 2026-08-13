import subprocess
from pathlib import Path


class PeerflixError(Exception):
    """Raised when peerflix fails to start."""


def stream(
    torrent_path: str | Path,
    vlc: bool = True,
    download_path: str | Path | None = None,
):
    torrent_path = Path(torrent_path)

    if not torrent_path.exists():
        raise PeerflixError(f"Torrent file not found: {torrent_path}")

    cmd = ["peerflix", str(torrent_path)]

    if vlc:
        cmd.append("--vlc")

    if download_path:
        download_path = Path(download_path)
        download_path.mkdir(parents=True, exist_ok=True)
        cmd.extend(["--path", str(download_path)])

    subprocess.run(cmd, check=True)
