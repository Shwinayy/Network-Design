from __future__ import annotations

import hashlib
import random
from pathlib import Path
from typing import Iterable, List


def chunk_bytes(data: bytes, chunk_size: int) -> List[bytes]:
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def should_drop(probability: float, rng: random.Random) -> bool:
    return probability > 0.0 and rng.random() < probability


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def ensure_parent(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def pct_to_prob(rate: float) -> float:
    return rate / 100.0 if rate > 1.0 else rate
