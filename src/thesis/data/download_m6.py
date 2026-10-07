"""Fetch the official M6 files from the organisers' repository.

Source: https://github.com/Mcompetitions/M6-methods
  data_files -> data/raw/m6/           (asset prices, all team submissions, leaderboard; not in git)
  code_files -> literature/m6_official/ (organisers' scoring and hypothesis code, kept for reference)
Run:    python -m thesis.data.download_m6
"""
from __future__ import annotations

import urllib.parse
import urllib.request

from thesis.paths import RAW_M6, ROOT, load_config

M6_OFFICIAL = ROOT / "literature" / "m6_official"


def fetch(base: str, rel: str, dest_dir) -> None:
    dest = dest_dir / rel.replace("IJF paper/", "ijf_").replace(" ", "_")
    if dest.exists():
        print("exists ", dest.relative_to(ROOT))
        return
    url = f"{base}/{urllib.parse.quote(rel)}"
    print("fetch  ", url)
    urllib.request.urlretrieve(url, dest)
    print("saved  ", dest.relative_to(ROOT), f"{dest.stat().st_size/1e6:.1f} MB")


def main() -> None:
    cfg = load_config()["m6"]
    M6_OFFICIAL.mkdir(parents=True, exist_ok=True)
    for rel in cfg["data_files"]:
        fetch(cfg["repo_raw"], rel, RAW_M6)
    for rel in cfg["code_files"]:
        fetch(cfg["repo_raw"], rel, M6_OFFICIAL)


if __name__ == "__main__":
    main()
