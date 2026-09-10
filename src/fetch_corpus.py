"""Download the Project Gutenberg corpora, by exact ID, into the train/test split.

Deterministic: the same IDs give the same bytes. The Wikipedia portion is a random
sample and lives in fetch_wiki.py, which is explicitly not reproducible.
"""

from __future__ import annotations

import pathlib
import sys
import urllib.request

UA = {"User-Agent": "keyboard-layout-study/1.0 (personal research)"}

BOOKS = [
    # (gutenberg id, filename, split directory)
    (34811, "buddenbrooks", "de_train"),
    (7205, "zarathustra", "de_train"),
    (5323, "effi_briest", "de_train"),
    (2407, "werther", "de_train"),
    (2229, "faust", "de_test"),
    (22367, "verwandlung", "de_test"),
    (12108, "tod_venedig", "de_test"),
    (1342, "pride_prejudice", "train"),
    (2701, "moby_dick", "train"),
    (1661, "sherlock", "train"),
    (84, "frankenstein", "train"),
    (2600, "war_and_peace", "train"),
    (98, "two_cities", "test"),
    (11, "alice", "test"),
    (1400, "great_expectations", "test"),
]


def fetch(pg_id: int) -> bytes:
    url = f"https://www.gutenberg.org/cache/epub/{pg_id}/pg{pg_id}.txt"
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=90).read()


def main() -> int:
    root = pathlib.Path("corpus")
    failures = 0
    for pg_id, name, split in BOOKS:
        d = root / split
        d.mkdir(parents=True, exist_ok=True)
        out = d / f"{name}.txt"
        if out.exists() and out.stat().st_size > 10_000:
            print(f"  have  {split}/{name}.txt")
            continue
        try:
            data = fetch(pg_id)
        except Exception as e:
            print(f"  FAIL  {split}/{name} (id {pg_id}): {e}")
            failures += 1
            continue
        out.write_bytes(data)
        print(f"  got   {split}/{name}.txt  {len(data):,} bytes")
    print("\nNow run: python fetch_wiki.py")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
