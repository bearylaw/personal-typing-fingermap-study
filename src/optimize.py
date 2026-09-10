"""Simulated annealing over the 32! assignment space, with restarts and a 2-opt polish.

Search is done exclusively against the TRAIN corpus and Model A. Everything used to
judge the winner afterwards (test corpus, Model B, model-free counters) is withheld from
the search on purpose.
"""

from __future__ import annotations

import math
import random
import sys
import time

import numpy as np

import data
import fastscore as fs
import layouts

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def anneal(fc: fs.FastCorpus, seed: int, iters: int = 260_000,
           t0: float = 60.0, t1: float = 0.05,
           pinned: dict[int, int] | None = None) -> tuple[np.ndarray, float]:
    """pinned maps char_id -> slot_id for characters that must not move."""
    rng = random.Random(seed)
    free = [c for c in range(32) if not pinned or c not in pinned]

    perm = np.arange(32)
    if pinned:
        used = set(pinned.values())
        rest = [s for s in range(32) if s not in used]
        rng.shuffle(rest)
        it = iter(rest)
        for c in range(32):
            perm[c] = pinned[c] if c in pinned else next(it)
    else:
        p = list(range(32))
        rng.shuffle(p)
        perm = np.array(p)

    cur = fs.effort(perm, fc)
    best, best_perm = cur, perm.copy()
    decay = (t1 / t0) ** (1.0 / iters)
    t = t0
    for _ in range(iters):
        a, b = rng.sample(free, 2)
        perm[a], perm[b] = perm[b], perm[a]
        cand = fs.effort(perm, fc)
        d = cand - cur
        if d <= 0 or rng.random() < math.exp(-d / t):
            cur = cand
            if cur < best:
                best, best_perm = cur, perm.copy()
        else:
            perm[a], perm[b] = perm[b], perm[a]
        t *= decay
    return best_perm, best


def polish(perm: np.ndarray, fc: fs.FastCorpus,
           pinned: dict[int, int] | None = None) -> tuple[np.ndarray, float]:
    """Exhaustive pairwise swaps until no single swap improves. Guarantees 2-optimality."""
    free = [c for c in range(32) if not pinned or c not in pinned]
    perm = perm.copy()
    cur = fs.effort(perm, fc)
    improved = True
    while improved:
        improved = False
        for i in range(len(free)):
            for j in range(i + 1, len(free)):
                a, b = free[i], free[j]
                perm[a], perm[b] = perm[b], perm[a]
                cand = fs.effort(perm, fc)
                if cand < cur - 1e-12:
                    cur = cand
                    improved = True
                else:
                    perm[a], perm[b] = perm[b], perm[a]
    return perm, cur


def search(fc: fs.FastCorpus, restarts: int, iters: int,
           pinned: dict[int, int] | None = None, label: str = "") -> tuple[np.ndarray, float, list]:
    results = []
    best, best_perm = float("inf"), None
    for s in range(restarts):
        t0 = time.time()
        p, v = anneal(fc, seed=1000 + s, iters=iters, pinned=pinned)
        p, v = polish(p, fc, pinned)
        results.append(v)
        if v < best:
            best, best_perm = v, p
        print(f"   {label}restart {s + 1}/{restarts}: {v:9.3f} "
              f"(best {best:9.3f}) [{time.time() - t0:.0f}s]", flush=True)
    return best_perm, best, results


def pin_from_qwertz(chars: str) -> dict[int, int]:
    """Pin characters to the slots they occupy on QWERTZ (e.g. for Ctrl+Z/X/C/V)."""
    slot_idx = {s: i for i, s in enumerate(fs.SLOTS_32)}
    m = layouts.to_mapping("QWERTZ")
    return {fs.CIDX[c]: slot_idx[m[c]] for c in chars}


if __name__ == "__main__":
    profile = sys.argv[1] if len(sys.argv) > 1 else "dev-at"
    restarts = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    iters = int(sys.argv[3]) if len(sys.argv) > 3 else 260_000

    base = data.base_corpora()
    train, _ = data.mixes(base, profile)
    fc = fs.FastCorpus(train)

    print(f"optimising for profile '{profile}' on TRAIN only")
    print(f"reference: QWERTZ = {fs.effort(fs.mapping_to_perm(layouts.to_mapping('QWERTZ')), fc):.2f}, "
          f"best published = "
          f"{min(fs.effort(fs.mapping_to_perm(layouts.to_mapping(n)), fc) for n in layouts.ALL if n != 'QWERTZ'):.2f}")
    print()

    print("A. unconstrained")
    perm, val, runs = search(fc, restarts, iters)
    s = fs.perm_to_string(perm)
    print(f"\n   best {val:.3f}   spread across restarts: "
          f"{min(runs):.2f} .. {max(runs):.2f} (sd {np.std(runs):.2f})")
    print(layouts.render(s, "   LAYOUT-A"))
    print(f"   string: {s}")

    print("\nB. with z x c v pinned to their QWERTZ keys (Ctrl-shortcut compatible)")
    pinned = pin_from_qwertz("zxcv")
    perm2, val2, runs2 = search(fc, max(3, restarts // 2), iters, pinned=pinned)
    s2 = fs.perm_to_string(perm2)
    print(f"\n   best {val2:.3f}  (costs {100 * (val2 - val) / val:+.2f}% vs unconstrained)")
    print(layouts.render(s2, "   LAYOUT-B"))
    print(f"   string: {s2}")

    with open(f"result_{profile}.txt", "w", encoding="utf-8") as f:
        f.write(f"{s}\n{s2}\n")
    print(f"\nwritten to result_{profile}.txt")
