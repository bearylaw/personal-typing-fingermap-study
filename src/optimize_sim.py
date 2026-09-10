"""Optimise against the mechanics instead of against my opinions.

Two objectives, neither of which contains a comfort judgement:

  forced   total same-finger travel per character, over lags 1-4.
           Completely parameter-free: geometry and corpus counts.

  time     simulated milliseconds per character from the parallel-finger model,
           at a demanding sequencing rate where the layout actually binds.

Whatever comes out of this is the mechanically best layout for the corpus. It is worth
comparing with what the hand-weighted search produced, because the difference between
them is exactly the part of ZEHN that rests on my judgement rather than on physics.
"""

from __future__ import annotations

import math
import random
import sys

import numpy as np

import data
import layouts
import simfast
from keyboard import KEYS, SLOTS_32, dist

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def forced_tables(sc: simfast.SimCorpus):
    D = simfast.travel_table()
    return D, sc.L


def make_objective(kind: str, sc: simfast.SimCorpus, gap: float = 30.0):
    if kind == "forced":
        D = simfast.travel_table()

        def obj(perm):
            sub = D[np.ix_(perm, perm)]
            return float(sum((sc.L[l] * sub).sum() for l in range(simfast.MAX_LAG)))
        return obj

    sim = simfast.SimScorer(gap=gap)

    def obj(perm):
        return sim.ms_per_char(perm, sc)
    return obj


def anneal(obj, seed: int, iters: int = 300_000, t0: float = 2.0, t1: float = 0.002):
    rng = random.Random(seed)
    p = list(range(32))
    rng.shuffle(p)
    perm = np.array(p)
    cur = obj(perm)
    best, best_perm = cur, perm.copy()
    decay = (t1 / t0) ** (1.0 / iters)
    t = t0
    for _ in range(iters):
        a, b = rng.sample(range(32), 2)
        perm[a], perm[b] = perm[b], perm[a]
        cand = obj(perm)
        d = cand - cur
        if d <= 0 or rng.random() < math.exp(-d / t):
            cur = cand
            if cur < best:
                best, best_perm = cur, perm.copy()
        else:
            perm[a], perm[b] = perm[b], perm[a]
        t *= decay
    return best_perm, best


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


def scale_for(kind: str) -> tuple[float, float]:
    # annealing temperatures matched to each objective's units
    return (2.0, 0.002) if kind == "forced" else (6.0, 0.006)


def main() -> None:
    profile = sys.argv[1] if len(sys.argv) > 1 else "dev-at"
    restarts = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    iters = int(sys.argv[3]) if len(sys.argv) > 3 else 300_000

    base = data.base_corpora()
    train, _ = data.mixes(base, profile)
    sc = simfast.SimCorpus(train)

    out = {}
    for kind in ("forced", "time"):
        obj = make_objective(kind, sc)
        t0, t1 = scale_for(kind)
        rivals = {n: obj(simfast.mapping_to_perm(layouts.to_mapping(n)))
                  for n in ("QWERTZ", "AdNW", "AdNWzjßf", "KOY")}
        print(f"\n### objective: {kind}")
        for n, v in sorted(rivals.items(), key=lambda kv: kv[1]):
            print(f"   {n:<10} {v:10.4f}")
        best, bv = None, float("inf")
        vals = []
        for s in range(restarts):
            p, v = anneal(obj, seed=4000 + 17 * s, iters=iters, t0=t0, t1=t1)
            p, v = polish(p, obj)
            vals.append(v)
            if v < bv:
                best, bv = p, v
            print(f"   restart {s + 1}/{restarts}: {v:10.4f} (best {bv:10.4f})", flush=True)
        s_out = simfast.perm_to_string(best)
        out[kind] = s_out
        gain = 100 * (min(v for n, v in rivals.items() if n != "QWERTZ") - bv) / bv
        print(f"   spread {min(vals):.4f}..{max(vals):.4f} (sd {np.std(vals):.4f})")
        print(f"   best published is {gain:+.2f}% away from this optimum")
        print(layouts.render(s_out, f"   MECH-{kind.upper()}"))
        print(f"   string: {s_out}")

    with open(f"result_sim_{profile}.txt", "w", encoding="utf-8") as f:
        f.write(out["time"] + "\n")
        f.write(out["forced"] + "\n")
    print(f"\nwritten to result_sim_{profile}.txt")


if __name__ == "__main__":
    main()
