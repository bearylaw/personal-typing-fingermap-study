"""Vectorised Model-A scorer, for use inside the optimiser.

The scoring problem is a quadratic assignment problem: 32 characters into 32 slots, with
a linear term (key comfort), two quadratic terms (bigrams, skipgrams) and a cubic term
(trigram redirects). With a 32-character alphabet the tables are tiny, so a full
re-evaluation is a handful of numpy operations rather than a pass over the corpus.

verify() checks this against the slow, readable implementation in metrics.py.
"""

from __future__ import annotations

import numpy as np

from keyboard import (
    FINGER_RANK,
    KEYS,
    PITCH,
    SLOTS_32,
    TH,
    dist,
    hand,
    is_stretch,
    travel_from_home,
)
from metrics import (
    A_ALTERNATE,
    A_BALANCE,
    A_FINGER_COST,
    A_REDIRECT,
    A_REDIRECT_NOIDX,
    A_ROLL_IN,
    A_ROLL_OUT,
    A_ROW_PEN,
    A_ROWJUMP,
    A_SCISSOR,
    A_SFB,
    A_SFB_DIST,
    A_SKIP,
    A_STRETCH,
    A_TARGET_LOAD,
    A_TRAVEL,
)

CHARS = "abcdefghijklmnopqrstuvwxyzäöüß,."
assert len(CHARS) == 32
CIDX = {c: i for i, c in enumerate(CHARS)}
NS = len(SLOTS_32)


def _slot_key_cost() -> np.ndarray:
    out = np.zeros(NS)
    for i, s in enumerate(SLOTS_32):
        k = KEYS[s]
        c = A_FINGER_COST[k.finger] * (1.0 + A_TRAVEL * travel_from_home(k) / PITCH)
        c += A_ROW_PEN[k.row]
        if is_stretch(s):
            c += A_STRETCH
        out[i] = c
    return out


def _slot_pair_cost() -> np.ndarray:
    """P[i, j] = cost of typing slot j immediately after slot i (different characters)."""
    P = np.zeros((NS, NS))
    for i, si in enumerate(SLOTS_32):
        ki = KEYS[si]
        for j, sj in enumerate(SLOTS_32):
            kj = KEYS[sj]
            if hand(ki.finger) != hand(kj.finger):
                P[i, j] = A_ALTERNATE
                continue
            if ki.finger == kj.finger:
                if i == j:
                    P[i, j] = 0.0          # a repeated letter, no repositioning
                else:
                    P[i, j] = A_SFB + A_SFB_DIST * dist(ki, kj) / PITCH
                continue
            ra, rb = FINGER_RANK[ki.finger], FINGER_RANK[kj.finger]
            rowdiff = abs(ki.row - kj.row)
            pen = A_ROWJUMP * rowdiff
            if abs(ra - rb) == 1 and rowdiff >= 2:
                P[i, j] = A_SCISSOR + pen
            else:
                P[i, j] = pen + (A_ROLL_IN if rb < ra else A_ROLL_OUT)
    return P


def _slot_skip_cost() -> np.ndarray:
    Q = np.zeros((NS, NS))
    for i, si in enumerate(SLOTS_32):
        for j, sj in enumerate(SLOTS_32):
            if i != j and KEYS[si].finger == KEYS[sj].finger:
                Q[i, j] = A_SKIP
    return Q


def _redirect_table() -> np.ndarray:
    """R[fa, fb, fc] = trigram redirect penalty for that finger triple."""
    R = np.zeros((8, 8, 8))
    for fa in range(8):
        for fb in range(8):
            for fc in range(8):
                if hand(fa) != hand(fb) or hand(fb) != hand(fc):
                    continue
                if fa == fb or fb == fc:
                    continue
                d1 = FINGER_RANK[fb] - FINGER_RANK[fa]
                d2 = FINGER_RANK[fc] - FINGER_RANK[fb]
                if d1 * d2 < 0:
                    pen = A_REDIRECT
                    if not any(FINGER_RANK[f] == 1 for f in (fa, fb, fc)):
                        pen += A_REDIRECT_NOIDX
                    R[fa, fb, fc] = pen
    return R


SLOT_KEY: np.ndarray
SLOT_PAIR: np.ndarray
SLOT_SKIP: np.ndarray
REDIRECT: np.ndarray
SLOT_FINGER: np.ndarray
TARGET = np.array([A_TARGET_LOAD[f] for f in range(8)])


def rebuild() -> None:
    """Recompute the slot tables. Must be called after keyboard.set_variant()."""
    global SLOT_KEY, SLOT_PAIR, SLOT_SKIP, REDIRECT, SLOT_FINGER
    SLOT_KEY = _slot_key_cost()
    SLOT_PAIR = _slot_pair_cost()
    SLOT_SKIP = _slot_skip_cost()
    REDIRECT = _redirect_table()
    SLOT_FINGER = np.array([KEYS[s].finger for s in SLOTS_32], dtype=np.int64)


rebuild()


class FastCorpus:
    """Corpus n-grams packed into arrays indexed by character id."""

    def __init__(self, ng, trigram_coverage: float = 0.995):
        self.name = ng.name
        self.total = float(ng.total)

        self.u = np.zeros(32)
        for c, n in ng.unigrams.items():
            self.u[CIDX[c]] = n

        self.W = np.zeros((32, 32))
        for (a, b), n in ng.bigrams.items():
            self.W[CIDX[a], CIDX[b]] = n

        self.S = np.zeros((32, 32))
        for (a, c), n in ng.skipgrams.items():
            self.S[CIDX[a], CIDX[c]] = n

        items = sorted(ng.trigrams.items(), key=lambda kv: -kv[1])
        tot = sum(ng.trigrams.values()) or 1.0
        keep, acc = [], 0.0
        for k, v in items:
            keep.append((k, v))
            acc += v
            if acc / tot >= trigram_coverage:
                break
        self.ta = np.array([CIDX[k[0]] for k, _ in keep], dtype=np.int64)
        self.tb = np.array([CIDX[k[1]] for k, _ in keep], dtype=np.int64)
        self.tc = np.array([CIDX[k[2]] for k, _ in keep], dtype=np.int64)
        self.tn = np.array([v for _, v in keep], dtype=float)
        self.trigram_kept = len(keep)
        self.trigram_total = len(ng.trigrams)


def effort(perm: np.ndarray, fc: FastCorpus) -> float:
    """Model-A effort units per 1000 characters. perm[char_id] = slot_id."""
    linear = float(fc.u @ SLOT_KEY[perm])
    sub = SLOT_PAIR[np.ix_(perm, perm)]
    quad = float((fc.W * sub).sum())
    skip = float((fc.S * SLOT_SKIP[np.ix_(perm, perm)]).sum())

    f = SLOT_FINGER[perm]
    cube = float(REDIRECT[f[fc.ta], f[fc.tb], f[fc.tc]] @ fc.tn)

    load = np.bincount(f, weights=fc.u, minlength=8)
    share = load / max(load.sum(), 1e-9)
    balance = A_BALANCE * float(((share - TARGET) ** 2).sum()) * fc.total

    return 1000.0 * (linear + quad + skip + cube + balance) / fc.total


def mapping_to_perm(mapping: dict[str, str]) -> np.ndarray:
    """See simfast.mapping_to_perm -- same contract, same QWERTZ caveat."""
    slot_idx = {s: i for i, s in enumerate(SLOTS_32)}
    perm = np.full(32, -1, dtype=np.int64)
    used = set()
    for c, s in mapping.items():
        if c in CIDX and s in slot_idx:
            perm[CIDX[c]] = slot_idx[s]
            used.add(slot_idx[s])
    spare = [i for i in range(NS) if i not in used]
    for ci in range(32):
        if perm[ci] < 0:
            perm[ci] = spare.pop(0)
    assert sorted(perm.tolist()) == list(range(32)), "mapping_to_perm produced a collision"
    return perm


def perm_to_string(perm: np.ndarray) -> str:
    out = [""] * 32
    for ci, si in enumerate(perm):
        out[si] = CHARS[ci]
    return "".join(out)
