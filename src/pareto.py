"""How much benefit survives if you only move a few keys?

A full 32-key relearn costs weeks. This finds the best layout that differs from QWERTZ in
at most k positions, for a range of k, so the trade-off is visible instead of assumed.

The objective is the parallel-finger simulator (mechanics), not the weighted effort model,
so these numbers carry the same assumptions as the rest of the study and no more.
"""

from __future__ import annotations

import math
import random
import sys

import numpy as np

import data
import layouts
import simfast
from frontier import weak_share

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def hamming(a: np.ndarray, b: np.ndarray) -> int:
    return int((a != b).sum())


def anneal_limited(sim, sc, ref, max_moved, seed, iters=140_000):
    rng = random.Random(seed)
    perm = ref.copy()
    cur = sim.ms_per_char(perm, sc)
    best, bperm = cur, perm.copy()
    t0, t1 = 4.0, 0.004
    decay = (t1 / t0) ** (1.0 / iters)
    t = t0
    for _ in range(iters):
        a, b = rng.sample(range(32), 2)
        perm[a], perm[b] = perm[b], perm[a]
        if hamming(perm, ref) > max_moved:
            perm[a], perm[b] = perm[b], perm[a]
            t *= decay
            continue
        c = sim.ms_per_char(perm, sc)
        d = c - cur
        if d <= 0 or rng.random() < math.exp(-d / t):
            cur = c
            if cur < best:
                best, bperm = c, perm.copy()
        else:
            perm[a], perm[b] = perm[b], perm[a]
        t *= decay
    return bperm, best


def polish_limited(perm, sim, sc, ref, k):
    perm = perm.copy()
    cur = sim.ms_per_char(perm, sc)
    improved = True
    while improved:
        improved = False
        for i in range(32):
            for j in range(i + 1, 32):
                perm[i], perm[j] = perm[j], perm[i]
                if hamming(perm, ref) > k:
                    perm[i], perm[j] = perm[j], perm[i]
                    continue
                c = sim.ms_per_char(perm, sc)
                if c < cur - 1e-12:
                    cur, improved = c, True
                else:
                    perm[i], perm[j] = perm[j], perm[i]
    return perm, cur


def main() -> None:
    profile = sys.argv[1] if len(sys.argv) > 1 else "dev-at"
    base = data.base_corpora()
    train, test = data.mixes(base, profile)
    sc_tr, sc_te = simfast.SimCorpus(train), simfast.SimCorpus(test)
    sim = simfast.SimScorer(gap=30.0)

    u_te = np.zeros(32)
    for c, n in test.unigrams.items():
        u_te[simfast.CIDX[c]] = n

    ref = simfast.mapping_to_perm(layouts.to_mapping("QWERTZ"))
    q = sim.ms_per_char(ref, sc_te)

    try:
        full = open(f"result_final_{profile}.txt", encoding="utf-8").readline().strip()
        fperm = simfast.mapping_to_perm(layouts.to_mapping("Z", full))
        full_te = sim.ms_per_char(fperm, sc_te)
        moved = hamming(fperm, ref)
    except OSError:
        full_te, moved = None, None

    print(f"QWERTZ on held-out text: {q:.3f} ms/char")
    if full_te:
        print(f"full layout moves {moved} keys -> {full_te:.3f} ms/char "
              f"({100 * (full_te - q) / q:+.1f}%)")
    gain_full = (q - full_te) if full_te else None

    print(f"\n{'keys moved':>11}{'train':>10}{'test':>10}{'vs QWERTZ':>12}"
          f"{'% of full gain':>16}{'weak%':>8}   layout")
    print("-" * 118)
    for k in (2, 4, 6, 8, 10, 12, 16, 20, 26, 32):
        best, bv = None, float("inf")
        for s in range(3):
            p, v = anneal_limited(sim, sc_tr, ref, k, seed=600 + 31 * k + s)
            p, v = polish_limited(p, sim, sc_tr, ref, k)
            if v < bv:
                best, bv = p, v
        tv = sim.ms_per_char(best, sc_te)
        pct = 100 * (tv - q) / q
        share = 100 * (q - tv) / gain_full if gain_full else float("nan")
        print(f"{hamming(best, ref):>11}{bv:>10.3f}{tv:>10.3f}{pct:>11.1f}%"
              f"{share:>15.0f}%{weak_share(best, u_te):>8.1f}   {simfast.perm_to_string(best)}",
              flush=True)

    print("\nThe last column that matters is '% of full gain': how much of a complete")
    print("relearn you capture for a given number of keys moved.")


if __name__ == "__main__":
    main()
