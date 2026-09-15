from typing import TypedDict


class CrimeData(TypedDict):
    category_id: int | None
    title: str
    street: str
    lat: float | None
    lon: float | None
