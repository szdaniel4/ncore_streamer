from pathlib import Path
from urllib.parse import unquote, urljoin

import requests
from bs4 import BeautifulSoup


class NcoreLoginError(Exception):
    """Raised when nCore login fails."""


class NcoreDownloadError(Exception):
    """Raised when nCore torrent download fails."""


class NcoreClient:
    BASE_URL = "https://ncore.pro"

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0.0.0 Safari/537.36"
            )
        })

    def login(self) -> bool:
        response = self.session.get(
            f"{self.BASE_URL}/login.php",
            timeout=15,
        )

        response.raise_for_status()

        if 'id="login"' not in response.text:
            raise NcoreLoginError(
                "Login form not found. "
                "The nCore page may have changed."
            )

        data = {
            "nev": self.username,
            "pass": self.password,
        }

        response = self.session.post(
            f"{self.BASE_URL}/login.php",
            data=data,
            timeout=15,
            allow_redirects=True,
        )

        response.raise_for_status()

        if "Username or password did not match" in response.text:
            raise NcoreLoginError(
                "Incorrect username or password."
            )

        if self.username not in response.text:
            raise NcoreLoginError(
                "Login could not be verified."
            )

        return True

    def download_torrent(
        self,
        torrent_id: int,
        destination_dir: str | Path,
        suggested_name: str | None = None,
    ) -> Path:
        download_url = self._get_download_url(torrent_id)

        response = self.session.get(
            download_url,
            timeout=30,
        )

        response.raise_for_status()

        content = response.content

        if not self._looks_like_torrent_file(content):
            raise NcoreDownloadError(
                "The download endpoint did not return a valid .torrent file."
            )

        target_dir = Path(destination_dir).expanduser()
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = self._resolve_torrent_filename(
            response.headers.get("Content-Disposition"),
            torrent_id,
            suggested_name,
        )

        file_path = target_dir / filename

        with file_path.open("wb") as file_handle:
            file_handle.write(content)

        return file_path

    def _get_download_url(self, torrent_id: int) -> str:
        details_response = self.session.get(
            f"{self.BASE_URL}/torrents.php",
            params={
                "action": "details",
                "id": torrent_id,
            },
            timeout=15,
        )

        details_response.raise_for_status()

        soup = BeautifulSoup(details_response.text, "html.parser")

        for link in soup.select("a[href]"):
            href = link.get("href", "")

            if not href:
                continue

            if any(
                pattern in href
                for pattern in (
                    "download.php",
                    "action=download",
                    "/download/",
                )
            ):
                return urljoin(self.BASE_URL, href)

        raise NcoreDownloadError(
            "Could not find a torrent download link on the details page."
        )

    @staticmethod
    def _looks_like_torrent_file(content: bytes) -> bool:
        stripped = content.lstrip()

        if not stripped:
            return False

        if stripped.startswith(b"<"):
            return False

        return stripped[:1] in {b"d", b"l", b"i"} or stripped[:1].isdigit()

    @staticmethod
    def _resolve_torrent_filename(
        content_disposition: str | None,
        torrent_id: int,
        suggested_name: str | None,
    ) -> str:
        filename = None

        if content_disposition:
            parts = [part.strip() for part in content_disposition.split(";")]

            for part in parts:
                if part.startswith("filename*="):
                    _, _, encoded_name = part.partition("''")
                    filename = unquote(encoded_name.strip('"'))
                    break

                if part.startswith("filename="):
                    filename = part.split("=", 1)[1].strip('"')
                    break

        if not filename:
            base_name = suggested_name or f"torrent_{torrent_id}"
            safe_name = "".join(
                character if character.isalnum() or character in "._- ()[]" else "_"
                for character in base_name
            ).strip()
            filename = safe_name or f"torrent_{torrent_id}"

            if not filename.endswith(".torrent"):
                filename = f"{filename}.torrent"

        return filename