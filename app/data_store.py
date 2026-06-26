from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=16)
def load_json(name: str) -> list[dict[str, Any]]:
    path = DATA_DIR / name
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def find_one(name: str, sku: str, marketplace: str) -> dict[str, Any] | None:
    sku = sku.upper()
    marketplace = marketplace.upper()
    for row in load_json(name):
        if row.get("sku", "").upper() == sku and row.get("marketplace", "").upper() == marketplace:
            return row
    return None

