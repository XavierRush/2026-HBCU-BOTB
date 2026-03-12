from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, HttpUrl


class Product(BaseModel):
    name: str
    category: str
    brand: str
    price: float
    key_features: list[str]
    description: str
    availability: Literal["in stock", "out of stock"]
    url: HttpUrl | None = None
