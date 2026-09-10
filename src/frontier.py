"""The trade-off no purely mechanical model can settle.

optimize_sim.py produced the fastest layout the simulator can find. It puts 47% of all
keystrokes on the pinkies and ring fingers, because the simulator does not know that a
pinky is weaker than an index finger. Geometry cannot tell you that; it is physiology.

So instead of picking a finger-strength weighting and pretending it is objective, this
maps the whole frontier: for each ceiling on weak-finger load, what is the fastest layout
that respects it? The published layouts are plotted on the same axes. You can then choose
your own point on the curve, and see exactly what each step costs.

Weak fingers = both pinkies and both ring fingers (fingers 0, 1, 6, 7).
"""

from __future__ import annotations

import math
import random
import sys

import numpy as np

import data
import layouts
import simfast
from keyboard import KEYS, SLOTS_32, TH

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WEAK = (0, 1, 6, 7)
SLOT_FINGER = np.array([KEYS[s].finger for s in SLOTS_32])
IS_WEAK = np.isin(SLOT_FINGER, WEAK).astype(float)


def weak_share(perm: np.ndarray, u: np.ndarray) -> float:
    """% of keystrokes falling on pinkies and ring fingers."""
    return 100.0 * float(u @ IS_WEAK[perm]) / float(u.sum())


def make_obj(sc: simfast.SimCorpus, u: np.ndarray, ceiling: float, gap: float = 30.0):
    sim = simfast.SimScorer(gap=gap)

    def obj(perm):
        t = sim.ms_per_char(perm, sc)
        w = weak_share(perm, u)
        if w > ceiling:
            t += 3.0 * (w - ceiling) ** 2      # steep barrier, not a trade-off weight
        return t

    def raw(perm):
        return sim.ms_per_char(perm, sc), weak_share(perm, u)

    return obj, raw


def anneal(obj, seed, iters=220_000, t0=6.0, t1=0.006):
    rng = random.Random(seed)
    p = list(range(32))
    rng.shuffle(p)
    perm = np.array(p)
    cur = obj(perm)
    best, bperm = cur, perm.copy()
    decay = (t1 / t0) ** (1.0 / iters)
    t = t0
    for _ in range(iters):
        a, b = rng.sample(range(32), 2)
        perm[a], perm[b] = perm[b], perm[a]
        c = obj(perm)
        d = c - cur
        if d <= 0 or rng.random() < math.exp(-d / t):
            cur = c
            if cur < best:
                best, bperm = cur, perm.copy()
        else:
            perm[a], perm[b] = perm[b], perm[a]
        t *= decay
    return bperm, best


def polish(perm, obj):
    perm = perm.copy()
    cur = obj(perm)
    improved = True
    while improved:
        improved = False
        for i in range(32):
            for j in range(i + 1, 32):
                perm[i], perm[j] = perm[j], perm[i]
                c = obj(perm)
                if c < cur - 1e-12:
                    cur, improved = c, True
                else:
                    perm[i], perm[j] = perm[j], perm[i]
    return perm, cur


def main() -> None:
    profile = sys.argv[1] if len(sys.argv) > 1 else "dev-at"
    restarts = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    iters = int(sys.argv[3]) if len(sys.argv) > 3 else 220_000

    base = data.base_corpora()
    train, test = data.mixes(base, profile)
    sc_train = simfast.SimCorpus(train)
    sc_test = simfast.SimCorpus(test)

    u = np.zeros(32)
    for c, n in train.unigrams.items():
        u[simfast.CIDX[c]] = n

    u_test = np.zeros(32)
    for c, n in test.unigrams.items():
        u_test[simfast.CIDX[c]] = n

    sim = simfast.SimScorer(gap=30.0)

    print("published layouts, for reference (TRAIN):")
    print(f"{'layout':<12}{'ms/char':>10}{'weak%':>9}")
    for n in layouts.ALL:
        p = simfast.mapping_to_perm(layouts.to_mapping(n))
        print(f"{n:<12}{sim.ms_per_char(p, sc_train):>10.3f}{weak_share(p, u):>9.1f}")

    print(f"\n{'ceiling':>8}{'ms/char':>10}{'weak%':>8}{'test ms/ch':>12}{'test weak%':>12}   layout")
    print("-" * 100)
    rows = []
    for ceiling in (28.0, 30.0, 32.0, 34.0, 36.0, 38.0, 41.0, 45.0, 50.0):
        obj, raw = make_obj(sc_train, u, ceiling)
        best, bv = None, float("inf")
        for s in range(restarts):
            p, v = anneal(obj, seed=9000 + int(ceiling) * 7 + s, iters=iters)
            p, v = polish(p, obj)
            if v < bv:
                best, bv = p, v
        ms, w = raw(best)
        ms_t = sim.ms_per_char(best, sc_test)
        w_t = weak_share(best, u_test)
        s_out = simfast.perm_to_string(best)
        rows.append((ceiling, ms, w, ms_t, w_t, s_out))
        print(f"{ceiling:>8.0f}{ms:>10.3f}{w:>8.1f}{ms_t:>12.3f}{w_t:>12.1f}   {s_out}",
              flush=True)

    with open(f"frontier_{profile}.txt", "w", encoding="utf-8") as f:
        for ceiling, ms, w, ms_t, w_t, s in rows:
            f.write(f"{ceiling}\t{ms}\t{w}\t{ms_t}\t{w_t}\t{s}\n")
    print(f"\nwritten to frontier_{profile}.txt")


if __name__ == "__main__":
    main()
