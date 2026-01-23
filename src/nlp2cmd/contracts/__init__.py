from __future__ import annotations

from pathlib import Path


def contracts_dir() -> Path:
    return Path(__file__).resolve().parent


__all__ = ["contracts_dir"]
