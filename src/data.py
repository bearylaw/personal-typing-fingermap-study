"""Corpus assembly with an explicit train/test split.

Split design — the point is that the optimiser must never see the text it is judged on,
and ideally not even the *genre* it is judged on:

    TRAIN   German literature (Gutenberg, pre-reform orthography)
            English literature (Gutenberg)
            Python stdlib, first slice

    TEST    German Wikipedia (contemporary orthography, encyclopaedic register)
            English literature, different authors
            Python stdlib, disjoint slice

Training on 19th-century novels and testing on modern Wikipedia is a deliberately hard
generalisation test: different century, different register, and a spelling reform in
between (daß -> dass moves real probability mass off ß onto s).
"""

from __future__ import annotations

import pathlib
import pickle
import sys

import corpora

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CACHE = pathlib.Path("cache")
CACHE.mkdir(exist_ok=True)

# Default mix for the user: an Austrian developer writing German prose, English prose
# and code. Weights are shares of typed characters.
PROFILES = {
    "dev-at":   {"de": 0.45, "en": 0.30, "code": 0.25},
    "german":   {"de": 1.00, "en": 0.00, "code": 0.00},
    "english":  {"de": 0.00, "en": 1.00, "code": 0.00},
    "code":     {"de": 0.00, "en": 0.00, "code": 1.00},
    "de-heavy": {"de": 0.70, "en": 0.20, "code": 0.10},
    "balanced": {"de": 0.34, "en": 0.33, "code": 0.33},
}


def _cached(name: str, build):
    p = CACHE / f"{name}.pkl"
    if p.exists():
        with p.open("rb") as f:
            return pickle.load(f)
    ng = build()
    with p.open("wb") as f:
        pickle.dump(ng, f)
    return ng


def _read(path: str) -> str:
    p = pathlib.Path(path)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def base_corpora() -> dict[str, corpora.Ngrams]:
    out = {}
    out["de_train"] = _cached("de_train", lambda: corpora.Ngrams(
        "de_train", corpora.load_dir("corpus/de_train")))
    out["en_train"] = _cached("en_train", lambda: corpora.Ngrams(
        "en_train", corpora.load_dir("corpus/train")))
    out["code_train"] = _cached("code_train", lambda: corpora.Ngrams(
        "code_train", corpora.load_python_stdlib(500, skip=0)))

    wiki_de = _read("corpus/_wiki_de.txt") or _read("corpus/_wiki_de_raw.txt")
    de_test_text = corpora.load_dir("corpus/de_test") + "\n" + wiki_de
    out["de_test"] = _cached("de_test", lambda: corpora.Ngrams("de_test", de_test_text))

    wiki_en = _read("corpus/_wiki_en.txt")
    en_test_text = corpora.load_dir("corpus/test") + "\n" + wiki_en
    out["en_test"] = _cached("en_test", lambda: corpora.Ngrams("en_test", en_test_text))

    out["code_test"] = _cached("code_test", lambda: corpora.Ngrams(
        "code_test", corpora.load_python_stdlib(400, skip=500)))
    return out


def mixes(base: dict[str, corpora.Ngrams], profile: str):
    w = PROFILES[profile]
    train = corpora.blend(
        [(base["de_train"], w["de"]), (base["en_train"], w["en"]), (base["code_train"], w["code"])],
        f"{profile}/train",
    )
    test = corpora.blend(
        [(base["de_test"], w["de"]), (base["en_test"], w["en"]), (base["code_test"], w["code"])],
        f"{profile}/test",
    )
    return train, test


if __name__ == "__main__":
    b = base_corpora()
    print(f"{'corpus':<12}{'chars':>12}   top letters")
    for k, ng in b.items():
        top = " ".join(f"{c}{100*n/ng.total:.1f}" for c, n in ng.unigrams.most_common(8))
        print(f"{k:<12}{ng.total:>12,}   {top}")
    print()
    for prof in ("dev-at", "german"):
        tr, te = mixes(b, prof)
        print(f"{prof}: train {tr.total:,.0f} units, test {te.total:,.0f} units")
