from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def get_user_config_dir() -> Path:
    """Return the user config directory for NLP2CMD.

    Precedence:
    - NLP2CMD_CONFIG_DIR
    - $XDG_CONFIG_HOME/nlp2cmd
    - ~/.config/nlp2cmd
    """

    explicit = os.environ.get("NLP2CMD_CONFIG_DIR")
    if explicit:
        return Path(explicit).expanduser()

    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg).expanduser() / "nlp2cmd"

    return Path.home() / ".config" / "nlp2cmd"


def _legacy_user_config_dir() -> Path:
    return Path.home() / ".nlp2cmd"


def _package_data_dir() -> Path:
    try:
        from importlib import resources

        return Path(resources.files("nlp2cmd").joinpath("data"))
    except Exception:
        pass

    pkg_dir = Path(__file__).resolve().parents[1]
    if (pkg_dir / "data").exists():
        return pkg_dir / "data"

    try:
        project_dir = Path(__file__).resolve().parents[3]
        if (project_dir / "data").exists():
            return project_dir / "data"
    except Exception:
        pass

    return Path(__file__).resolve().parents[2] / "data"


def find_data_files(
    *,
    explicit_path: Optional[str],
    default_filename: str,
) -> list[Path]:
    """Return a list of existing data file paths in merge order.

    Order (base -> overrides):
    - packaged data: nlp2cmd/data/<default_filename>
    - ./data/<default_filename> (project/local overrides)
    - ~/.nlp2cmd/<default_filename> (legacy)
    - ~/.config/nlp2cmd/<default_filename> (or NLP2CMD_CONFIG_DIR)
    - explicit_path (if provided)
    """

    out: list[Path] = []

    user_dir = get_user_config_dir()
    legacy_dir = _legacy_user_config_dir()

    candidates: list[Path] = [
        _package_data_dir() / default_filename,
        Path("data") / default_filename,
        Path("./data") / default_filename,
        legacy_dir / default_filename,
        user_dir / default_filename,
    ]

    if explicit_path:
        candidates.append(Path(explicit_path).expanduser())

    seen: set[str] = set()
    for p in candidates:
        try:
            rp = str(p.resolve())
        except Exception:
            rp = str(p)
        if rp in seen:
            continue
        seen.add(rp)

        try:
            if p.exists() and p.is_file():
                out.append(p)
        except Exception:
            continue

    return out


def find_data_file(
    *,
    explicit_path: Optional[str],
    default_filename: str,
) -> Optional[Path]:
    """Resolve a data/*.json file path.

    Order:
    - explicit_path (if provided and exists)
    - ./data/<default_filename>
    - search parent dirs of this file for a sibling data/<default_filename>
    """

    paths = find_data_files(explicit_path=explicit_path, default_filename=default_filename)
    return paths[-1] if paths else None


def data_file_write_path(*, explicit_path: Optional[str], default_filename: str) -> Path:
    """Resolve a writable path for a data file.

    If explicit_path is provided, it is used as-is.
    Otherwise, defaults to ./data/<default_filename> relative to current working directory.
    """

    if explicit_path:
        return Path(explicit_path).expanduser()
    return get_user_config_dir() / default_filename
