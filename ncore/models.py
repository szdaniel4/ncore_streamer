from dataclasses import dataclass
from typing import Optional


@dataclass
class Torrent:
    id: int
    name: str
    category: str
    size: str
    uploaded: str
    seeders: int
    leechers: int
    imdb_rating: Optional[float] = None
    imdb_title: Optional[str] = None

    def __str__(self) -> str:
        rating = (
            f"IMDb {self.imdb_rating}"
            if self.imdb_rating is not None
            else "IMDb -"
        )

        return (
            f"[{self.id}] {self.name}\n"
            f"    {self.size} | S: {self.seeders} | L: {self.leechers} | {rating}"
        )