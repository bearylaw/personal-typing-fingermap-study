"""Corpus loading, cleaning, and n-gram extraction.

The scored alphabet is deliberately restricted to the 32 characters that every layout
under test places in the main block, plus space. See LIMITATIONS in RESULTS.md.
"""

from __future__ import annotations

import io
import pathlib
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ALPHABET = set("abcdefghijklmnopqrstuvwxyzäöüß,.")
SCORED = ALPHABET | {" "}

_GUT_START = re.compile(r"\*\*\* ?START OF TH[EIS].*?\*\*\*", re.I | re.S)
_GUT_END = re.compile(r"\*\*\* ?END OF TH[EIS].*?\*\*\*", re.I | re.S)


def strip_gutenberg(text: str) -> str:
    m = _GUT_START.search(text)
    if m:
        text = text[m.end():]
    m = _GUT_END.search(text)
    if m:
        text = text[: m.start()]
    return text


def normalise(text: str) -> str:
    """Fold to the scored alphabet.

    Uppercase folds to lowercase (Shift is a separate hand and is charged to neither
    layout, so case does not discriminate between them). Typographic quotes, dashes and
    whitespace collapse. Everything outside the alphabet becomes a space, which models
    'some other key was pressed and the hands returned to rest' rather than pretending
    the characters were adjacent.
    """
    text = text.lower()
    text = text.replace("’", "'").replace("„", '"').replace("“", '"')
    text = text.replace("–", "-").replace("—", "-").replace(" ", " ")
    out = []
    prev_space = False
    for ch in text:
        if ch in ALPHABET:
            out.append(ch)
            prev_space = False
        else:
            if not prev_space:
                out.append(" ")
                prev_space = True
    return "".join(out)


def load_dir(path: str | pathlib.Path, gutenberg: bool = True) -> str:
    parts = []
    for f in sorted(pathlib.Path(path).glob("*.txt")):
        raw = f.read_text(encoding="utf-8", errors="replace")
        if gutenberg:
            raw = strip_gutenberg(raw)
        parts.append(raw)
    return "\n".join(parts)


def load_python_stdlib(limit_files: int, skip: int = 0) -> str:
    import sysconfig

    root = pathlib.Path(sysconfig.get_paths()["stdlib"])
    files = sorted(p for p in root.rglob("*.py") if "test" not in p.parts and "__pycache__" not in p.parts)
    chunk = files[skip: skip + limit_files]
    parts = []
    for f in chunk:
        try:
            parts.append(f.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
    return "\n".join(parts)


MAX_LAG = 4


class Ngrams:
    """Frequency tables for one corpus, already folded to the scored alphabet.

    `lags[L]` counts pairs of typed characters L keystrokes apart, ignoring whatever
    fell in between. The simulator needs these: a finger that pressed a key L strokes
    ago has had L sequencing intervals to travel to its next one, so how much a
    same-finger collision costs depends on L, not just on L == 1.
    """

    __slots__ = ("name", "unigrams", "bigrams", "trigrams", "skipgrams", "lags", "total")

    def __init__(self, name: str, text: str):
        self.name = name
        text = normalise(text)
        # keystroke sequence: letters and spaces both cost a stroke, but only letters
        # occupy a finger we care about
        seq = [c for c in text if c in SCORED]
        self.unigrams = Counter(c for c in seq if c in ALPHABET)
        self.total = sum(self.unigrams.values())

        bi: Counter = Counter()
        tri: Counter = Counter()
        lags: dict[int, Counter] = {L: Counter() for L in range(1, MAX_LAG + 1)}
        n = len(seq)
        for i in range(n):
            a = seq[i]
            if a not in ALPHABET:
                continue
            for L in range(1, MAX_LAG + 1):
                j = i + L
                if j >= n:
                    break
                b = seq[j]
                if b in ALPHABET:
                    lags[L][(a, b)] += 1
            if i + 1 < n and seq[i + 1] in ALPHABET:
                bi[(a, seq[i + 1])] += 1
                if i + 2 < n and seq[i + 2] in ALPHABET:
                    tri[(a, seq[i + 1], seq[i + 2])] += 1
        self.bigrams = bi
        self.trigrams = tri
        self.skipgrams = lags[2]
        self.lags = lags

    def __repr__(self):
        return f"<Ngrams {self.name} chars={self.total:,} bi={len(self.bigrams):,}>"


BLEND_SIZE = 1_000_000.0   # nominal characters, so blended counts stay readable


def blend(parts: list[tuple[Ngrams, float]], name: str) -> Ngrams:
    """Weighted mixture of corpora. Weights are shares of typed characters."""
    obj = Ngrams.__new__(Ngrams)
    obj.name = name
    obj.unigrams = Counter()
    obj.bigrams = Counter()
    obj.trigrams = Counter()
    obj.lags = {L: Counter() for L in range(1, MAX_LAG + 1)}
    for ng, w in parts:
        if ng.total == 0 or w == 0:
            continue
        scale = w * BLEND_SIZE / ng.total
        for k, v in ng.unigrams.items():
            obj.unigrams[k] += v * scale
        for k, v in ng.bigrams.items():
            obj.bigrams[k] += v * scale
        for k, v in ng.trigrams.items():
            obj.trigrams[k] += v * scale
        for L in range(1, MAX_LAG + 1):
            tgt = obj.lags[L]
            for k, v in ng.lags[L].items():
                tgt[k] += v * scale
    obj.skipgrams = obj.lags[2]
    obj.total = sum(obj.unigrams.values())
    return obj
