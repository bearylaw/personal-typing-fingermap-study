"""Which finger SHOULD press which key, on the QWERTZ letters you already have.

The letters do not move. The only thing under search is the finger assignment -- the
touch-typing discipline itself, which is convention rather than measurement. Standard
German ten-finger teaching is one particular assignment; this asks whether it is the best
one for the keys as they actually sit on an ISO board.

Parametrisation. Fingers are ordered left to right and hands do not cross, so an
assignment is fully described by where the boundaries fall in each row:

    LP | LR | LM | LI | RI | RM | RR | RP        7 boundaries per row

Each row gets its own 7 cut positions, non-decreasing across the row. That is the whole
search space: 21 integers for the three letter rows. The number row inherits the top
row's cuts, since almost no text drives it.

Resting positions follow the assignment rather than being fixed at ASDF/JKLÖ: each finger
rests on the median home-row key it owns. A discipline that gives the left index three
home-row keys should rest in the middle of them, not off to one side.

Objective is the parallel-finger simulator from simulate.py -- same mechanics, same three
physical constants, no comfort weights.
"""

from __future__ import annotations

import itertools
import math
import random
import sys

import numpy as np

import data
import layouts
from keyboard import KEYS, PITCH, dist
from simulate import DWELL, GAP, SPEED, T_MOVE, travel_time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Physical rows, left to right. The number row is carried along but not searched.
ROW_NUM = ["^", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "ß_key", "´"]
ROW_TOP = ["q", "w", "e", "r", "t", "z", "u", "i", "o", "p", "ü", "+"]
ROW_HOME = ["a", "s", "d", "f", "g", "h", "j", "k", "l", "ö", "ä", "#"]
ROW_BOT = ["<", "y", "x", "c", "v", "b", "n", "m", ",", ".", "-"]
LETTER_ROWS = [ROW_TOP, ROW_HOME, ROW_BOT]

CHARS = "abcdefghijklmnopqrstuvwxyzäöüß,."
CIDX = {c: i for i, c in enumerate(CHARS)}
MAX_LAG = 4
MAX_REACH = 58.0        # mm; beyond this a key is not credibly owned by that finger

# Anatomical column of each finger, used only to choose resting keys.
NATURAL_HOME = {0: "a", 1: "s", 2: "d", 3: "f", 4: "j", 5: "k", 6: "l", 7: "ö"}

# QWERTZ character -> physical slot (ß sits on the number row)
QWERTZ = layouts.to_mapping("QWERTZ")

STANDARD_CUTS = {
    # boundaries after column index i, i.e. how many columns each finger owns
    "top": (1, 2, 3, 5, 7, 8, 9, 12),      # q | w | e | r t | z u | i | o | p ü +
    "home": (1, 2, 3, 5, 7, 8, 9, 12),     # a | s | d | f g | h j | k | l | ö ä #
    "bot": (2, 3, 4, 6, 8, 9, 10, 11),     # < y | x | c | v b | n m | , | . | -
}


def cuts_to_fingers(cuts, ncols):
    """cuts is 8 non-decreasing end positions; returns finger index per column."""
    out = []
    f = 0
    for c in range(ncols):
        while f < 7 and c >= cuts[f]:
            f += 1
        out.append(f)
    return out


def build_assignment(cut_top, cut_home, cut_bot) -> dict[str, int] | None:
    """Physical slot -> finger, or None if the assignment is not physically credible."""
    amap: dict[str, int] = {}
    for row, cuts in ((ROW_TOP, cut_top), (ROW_HOME, cut_home), (ROW_BOT, cut_bot)):
        fingers = cuts_to_fingers(cuts, len(row))
        for slot, f in zip(row, fingers):
            amap[slot] = f
    # The number row is staggered 1.5u left of the top row, so number key i sits above
    # top-row key i-1 and takes that key's finger. '^' follows '1'.
    top_f = cuts_to_fingers(cut_top, len(ROW_TOP))
    for i, slot in enumerate(ROW_NUM):
        amap[slot] = top_f[max(0, min(i - 1, len(top_f) - 1))]

    home_owned: dict[int, list[str]] = {}
    for slot, f in amap.items():
        if slot in ROW_HOME:
            home_owned.setdefault(f, []).append(slot)
    if len(home_owned) < 8:
        return None                      # a finger with no home key has nowhere to rest

    # A finger rests on the owned home-row key nearest its anatomical column. The hand is
    # anchored by the index fingers on F and J; the others follow. Taking a median instead
    # would rest the left index on G whenever it owns F and G, which no typist does.
    rest = {}
    for f, slots in home_owned.items():
        rest[f] = min(slots, key=lambda s: abs(KEYS[s].x - KEYS[NATURAL_HOME[f]].x))
    for slot, f in amap.items():
        if dist(KEYS[slot], KEYS[rest[f]]) > MAX_REACH:
            return None
    return amap, rest


class Corpus:
    def __init__(self, ng):
        self.total = float(ng.total)
        self.u = np.zeros(32)
        for c, n in ng.unigrams.items():
            self.u[CIDX[c]] = n
        self.L = []
        for lag in range(1, MAX_LAG + 1):
            M = np.zeros((32, 32))
            for (a, b), n in ng.lags[lag].items():
                M[CIDX[a], CIDX[b]] = n
            self.L.append(M / self.total)


def evaluate(amap, rest, corpus, gap=GAP, dwell=DWELL,
             t_move=T_MOVE, speed=SPEED):
    """Simulated ms/char, plus load and travel, for one finger assignment."""
    slot_of = [QWERTZ[c] for c in CHARS]
    fing = np.array([amap[s] for s in slot_of])

    # stall matrix over the 32 characters
    n = 32
    D = np.zeros((n, n))
    same = np.zeros((n, n), dtype=bool)
    for i in range(n):
        for j in range(n):
            if fing[i] == fing[j] and i != j:
                same[i, j] = True
                D[i, j] = dist(KEYS[slot_of[i]], KEYS[slot_of[j]])

    ms = gap
    for lag in range(1, MAX_LAG + 1):
        stall = np.where(same,
                         np.maximum(0.0, dwell + t_move + speed * np.sqrt(np.maximum(D, 1e-9))
                                    - lag * gap),
                         0.0)
        ms += float((corpus.L[lag - 1] * stall).sum())

    load = np.bincount(fing, weights=corpus.u, minlength=8)
    share = 100.0 * load / load.sum()
    weak = share[0] + share[1] + share[6] + share[7]
    travel = sum(2.0 * dist(KEYS[slot_of[i]], KEYS[rest[fing[i]]]) * corpus.u[i]
                 for i in range(n)) / corpus.u.sum()
    return ms, weak, share, travel


def neighbours(cuts, ncols, rng):
    c = list(cuts)
    i = rng.randrange(8)
    c[i] += rng.choice((-1, 1))
    c[i] = max(0, min(ncols, c[i]))
    c.sort()
    return tuple(c)


def search(corpus, iters=120_000, seed=0, weak_cap=None):
    rng = random.Random(seed)
    cur = (STANDARD_CUTS["top"], STANDARD_CUTS["home"], STANDARD_CUTS["bot"])
    built = build_assignment(*cur)
    best_val = score(built, corpus, weak_cap)
    best = cur
    val = best_val
    t0, t1 = 3.0, 0.003
    decay = (t1 / t0) ** (1.0 / iters)
    t = t0
    for _ in range(iters):
        which = rng.randrange(3)
        cand = list(cur)
        ncols = (len(ROW_TOP), len(ROW_HOME), len(ROW_BOT))[which]
        cand[which] = neighbours(cur[which], ncols, rng)
        cand = tuple(cand)
        built = build_assignment(*cand)
        v = score(built, corpus, weak_cap)
        if v - val <= 0 or rng.random() < math.exp(-(v - val) / t):
            cur, val = cand, v
            if v < best_val:
                best_val, best = v, cand
        t *= decay
    return best, best_val


def score(built, corpus, weak_cap, travel_cap=None):
    if built is None:
        return 1e9
    amap, rest = built
    ms, weak, _, travel = evaluate(amap, rest, corpus)
    if weak_cap is not None and weak > weak_cap:
        ms += 2.0 * (weak - weak_cap) ** 2
    if travel_cap is not None and travel > travel_cap:
        ms += 0.5 * (travel - travel_cap) ** 2
    return ms


def search_box(corpus, iters, seed, weak_cap, travel_cap):
    """Minimise simulated time subject to hard caps on weak-finger load AND travel.

    This is the test that decides the whole question. The unconstrained search buys its
    speed by sending fingers further; capping travel and load at the standard
    discipline's own values asks whether there is any free improvement left.
    """
    rng = random.Random(seed)
    cur = (STANDARD_CUTS["top"], STANDARD_CUTS["home"], STANDARD_CUTS["bot"])
    val = score(build_assignment(*cur), corpus, weak_cap, travel_cap)
    best, best_val = cur, val
    t0, t1 = 3.0, 0.003
    decay = (t1 / t0) ** (1.0 / iters)
    t = t0
    for _ in range(iters):
        which = rng.randrange(3)
        cand = list(cur)
        ncols = (len(ROW_TOP), len(ROW_HOME), len(ROW_BOT))[which]
        cand[which] = neighbours(cur[which], ncols, rng)
        cand = tuple(cand)
        v = score(build_assignment(*cand), corpus, weak_cap, travel_cap)
        if v - val <= 0 or rng.random() < math.exp(-(v - val) / t):
            cur, val = cand, v
            if v < best_val:
                best_val, best = v, cand
        t *= decay
    return best, best_val


def show(name, cuts, corpus):
    built = build_assignment(*cuts)
    if built is None:
        print(f"{name}: not physically credible")
        return None
    amap, rest = built
    ms, weak, share, travel = evaluate(amap, rest, corpus)
    names = {0: "LP", 1: "LR", 2: "LM", 3: "LI", 4: "RI", 5: "RM", 6: "RR", 7: "RP"}
    print(f"\n{name}")
    print(f"  simulated {ms:.3f} ms/char   weak fingers {weak:.1f}%   "
          f"travel {travel:.2f} mm/char")
    print(f"  rest: " + "  ".join(f"{names[f]}->{rest[f]}" for f in range(8)))
    for row, label in ((ROW_TOP, "top "), (ROW_HOME, "home"), (ROW_BOT, "bot ")):
        cells = "  ".join(f"{('ß' if s == 'ß_key' else s):>2}:{names[amap[s]]}" for s in row)
        print(f"  {label} {cells}")
    print("  load: " + "  ".join(f"{names[f]} {share[f]:4.1f}%" for f in range(8)))
    return ms, weak, share, travel


def main():
    profile = sys.argv[1] if len(sys.argv) > 1 else "dev-at"
    base = data.base_corpora()
    train, test = data.mixes(base, profile)
    ctr, cte = Corpus(train), Corpus(test)

    print("=" * 78)
    print("WHICH FINGER SHOULD PRESS WHICH KEY  —  QWERTZ letters, assignment searched")
    print("=" * 78)
    std = (STANDARD_CUTS["top"], STANDARD_CUTS["home"], STANDARD_CUTS["bot"])
    show("STANDARD German ten-finger discipline (held-out)", std, cte)

    best, _ = None, None
    bv = 1e18
    for s in range(6):
        cand, v = search(ctr, iters=120_000, seed=s)
        if v < bv:
            best, bv = cand, v
    show("BEST unconstrained assignment (held-out)", best, cte)

    stdm = evaluate(*build_assignment(*std), cte)
    bestm = evaluate(*build_assignment(*best), cte)
    cap = stdm[1]
    bestw, _ = None, None
    bwv = 1e18
    for s in range(6):
        cand, v = search(ctr, iters=120_000, seed=100 + s, weak_cap=cap)
        if v < bwv:
            bestw, bwv = cand, v
    show(f"BEST assignment with weak-finger load held at or below standard's {cap:.1f}% "
         f"(held-out)", bestw, cte)

    # ---- the decisive test ---------------------------------------------------------
    print("\n" + "=" * 78)
    print("DECISIVE TEST: beat the standard discipline on simulated time while spending")
    print(f"no more finger travel and no more weak-finger load")
    print(f"(caps: travel <= {stdm[3]:.2f} mm/char, weak <= {stdm[1]:.1f}%)")
    print("=" * 78)
    boxed, bxv = None, 1e18
    for s in range(8):
        cand, v = search_box(ctr, 140_000, 300 + s, stdm[1], stdm[3])
        if v < bxv:
            boxed, bxv = cand, v
    r = show("BEST assignment inside the box (held-out)", boxed, cte)
    verdict = "unknown"
    if r is not None:
        ms, weak, _, travel = r
        ok = ms < stdm[0] - 0.01 and travel <= stdm[3] + 0.05 and weak <= stdm[1] + 0.1
        print(f"\n  standard : {stdm[0]:.3f} ms/char   {stdm[3]:.2f} mm/char   {stdm[1]:.1f}% weak")
        print(f"  found    : {ms:.3f} ms/char   {travel:.2f} mm/char   {weak:.1f}% weak")
        verdict = ("IMPROVEMENT FOUND" if ok else
                   "NO IMPROVEMENT - the standard assignment is Pareto-optimal here")
        print(f"\n  {verdict}")

    print("\n" + "=" * 78)
    print(f"time alone: standard {stdm[0]:.3f} -> best {bestm[0]:.3f} ms/char "
          f"({100 * (bestm[0] - stdm[0]) / stdm[0]:+.2f}%), but that costs travel "
          f"{stdm[3]:.1f} -> {bestm[3]:.1f} mm/char")
    print(f"and weak-finger load {stdm[1]:.1f}% -> {bestm[1]:.1f}%.")
    print("=" * 78)
    with open(f"fingermap_{profile}.txt", "w", encoding="utf-8") as f:
        f.write(repr({"standard": std, "best": best, "best_capped": bestw,
                      "boxed": boxed, "verdict": verdict}) + "\n")
    print(f"written to fingermap_{profile}.txt")


if __name__ == "__main__":
    main()
