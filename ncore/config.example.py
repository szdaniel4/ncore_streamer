from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

NCORE_URL = "https://ncore.pro"
NCORE_LOGIN_URL = f"{NCORE_URL}/login.php"

USERNAME = "my_username_here"
PASSWORD = "my_password_here"
TORRENT_DOWNLOAD_DIR = BASE_DIR.parent / "downloads"
PEERFLIX_DOWNLOAD_DIR = BASE_DIR.parent / "movies"
PEERFLIX_VLC = True
