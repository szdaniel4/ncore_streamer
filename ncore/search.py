import re
from typing import List

from bs4 import BeautifulSoup

from ncore.models import Torrent


class NcoreSearchError(Exception):
    """Raised when nCore search fails."""


class NcoreSearch:
    def __init__(self, client):
        self.client = client

    def search(self, query: str) -> List[Torrent]:
        """
        Search on nCore.

        Uses the client session, so the search
        is performed with the already logged-in session.
        """

        response = self.client.session.get(
            "https://ncore.pro/torrents.php",
            params={
                "mire": query,
            },
            timeout=15,
        )

        response.raise_for_status()

        return self._parse_results(response.text)

    def _parse_results(self, html: str) -> List[Torrent]:
        soup = BeautifulSoup(html, "html.parser")

        torrents = []

        for box in soup.select(".box_torrent"):
            torrent = self._parse_torrent(box)

            if torrent is not None:
                torrents.append(torrent)

        return torrents

    def _parse_torrent(self, box) -> Torrent | None:
        # Torrent details link
        link = box.select_one(
            'a[href*="torrents.php?action=details&id="]'
        )

        if not link:
            return None

        href = link.get("href", "")

        match = re.search(r"id=(\d+)", href)

        if not match:
            return None

        torrent_id = int(match.group(1))

        # Whole torrent name
        name = link.get("title") or link.get_text(strip=True)

        # Size
        size_element = box.select_one(".box_meret2")

        size = (
            size_element.get_text(" ", strip=True)
            if size_element
            else "?"
        )

        # Submit date
        uploaded_element = box.select_one(".box_feltoltve2")

        uploaded = (
            uploaded_element.get_text(" ", strip=True)
            if uploaded_element
            else "?"
        )

        # Seed
        seed_element = box.select_one(".box_s2")

        seeders = self._parse_int(
            seed_element.get_text(strip=True)
            if seed_element
            else "0"
        )

        # Leech
        leech_element = box.select_one(".box_l2")

        leechers = self._parse_int(
            leech_element.get_text(strip=True)
            if leech_element
            else "0"
        )

        # Category
        category = self._parse_category(box)

        # IMDb
        imdb_rating, imdb_title = self._parse_imdb(box)

        return Torrent(
            id=torrent_id,
            name=name,
            category=category,
            size=size,
            uploaded=uploaded,
            seeders=seeders,
            leechers=leechers,
            imdb_rating=imdb_rating,
            imdb_title=imdb_title,
        )

    @staticmethod
    def _parse_int(value: str) -> int:
        match = re.search(r"\d+", value)

        if not match:
            return 0

        return int(match.group())

    @staticmethod
    def _parse_category(box) -> str:
        image = box.select_one(".box_alap_img img")

        if not image:
            return "unknown"

        return (
            image.get("alt")
            or image.get("title")
            or "unknown"
        )

    @staticmethod
    def _parse_imdb(box):
        imdb = box.select_one(".infolink")

        if not imdb:
            return None, None

        text = imdb.get_text(" ", strip=True)

        rating_match = re.search(
            r"imdb:\s*([0-9]+(?:\.[0-9]+)?)",
            text,
            re.IGNORECASE,
        )

        rating = (
            float(rating_match.group(1))
            if rating_match
            else None
        )

        title_element = box.select_one(".siterank span")

        title = (
            title_element.get_text(strip=True)
            if title_element
            else None
        )

        return rating, title