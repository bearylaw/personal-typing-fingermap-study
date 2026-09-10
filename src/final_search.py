"""The decisive experiment.

Three facts are now established:

  * The published German layouts (AdNW, KOY) are excellent on the awkwardness measures
    -- scissors 0.1%, redirects 3.4-3.7%, home row 60% -- and on simulated time.
  * They pay for it by putting 41% of all keystrokes on the pinkies and ring fingers,
    against QWERTZ's 28%.
  * Optimising the parallel-finger simulator alone fixes the load but wrecks the
    awkwardness measures, because a timing model cannot see a scissor.

So the question that decides whether there is anything new here is precise:

    Is there a layout that matches AdNW on every awkwardness measure AND on simulated
    time, while carrying far less weak-finger load?

If yes, AdNW is not Pareto-optimal and the frontier is a real result. If no, AdNW is
close to the best that can be done and the honest answer is to use it.

Constraints are hard barriers set to AdNW's own values, not weights. Nothing is traded
off against anything; the search either finds a layout inside the box or it does not.
"""

from __future__ import annotations

import math
import random
import sys

import numpy as np

import data
import layouts
import simfast
from keyboard import FINGER_RANK, KEYS, SLOTS_32, hand
from metrics import Scorer

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NS = len(SLOTS_32)
SLOT_FINGER = np.array([KEYS[s].finger for s in SLOTS_32])
WEAK = np.isin(SLOT_FINGER, (0, 1, 6, 7)).astype(float)
HOME = np.array([1.0 if (KEYS[s].row == 3 and s not in ("g", "h", "ä")) else 0.0
                 for s in SLOTS_32])


def scissor_table() -> np.ndarray:
    S = np.zeros((NS, NS))
    for i, si in enumerate(SLOTS_32):
        ki = KEYS[si]
        for j, sj in enumerate(SLOTS_32):
            kj = KEYS[sj]
            if hand(ki.finger) != hand(kj.finger) or ki.finger == kj.finger:
                continue
            if abs(FINGER_RANK[ki.finger] - FINGER_RANK[kj.finger]) == 1 \
                    and abs(ki.row - kj.row) >= 2:
                S[i, j] = 1.0
    return S


def redirect_table() -> np.ndarray:
    R = np.zeros((8, 8, 8))
    for a in range(8):
        for b in range(8):
            for c in range(8):
                if hand(a) != hand(b) or hand(b) != hand(c):
                    continue
                if a == b or b == c:
                    continue
                if (FINGER_RANK[b] - FINGER_RANK[a]) * (FINGER_RANK[c] - FINGER_RANK[b]) < 0:
                    R[a, b, c] = 1.0
    return R


SCISSOR = scissor_table()
REDIRECT = redirect_table()


class Constrained:
    def __init__(self, ng, sc: simfast.SimCorpus, gap: float = 30.0):
        self.sim = simfast.SimScorer(gap=gap)
        self.sc = sc
        self.u = np.zeros(32)
        for c, n in ng.unigrams.items():
            self.u[simfast.CIDX[c]] = n
        self.u_sum = self.u.sum()

        self.W = np.zeros((32, 32))
        for (a, b), n in ng.bigrams.items():
            self.W[simfast.CIDX[a], simfast.CIDX[b]] = n
        self.W_sum = self.W.sum()

        items = sorted(ng.trigrams.items(), key=lambda kv: -kv[1])
        tot = sum(ng.trigrams.values())
        keep, acc = [], 0.0
        for k, v in items:
            keep.append((k, v))
            acc += v
            if acc / tot >= 0.995:
                break
        self.ta = np.array([simfast.CIDX[k[0]] for k, _ in keep])
        self.tb = np.array([simfast.CIDX[k[1]] for k, _ in keep])
        self.tc = np.array([simfast.CIDX[k[2]] for k, _ in keep])
        self.tn = np.array([v for _, v in keep], dtype=float)
        self.tri_sum = tot

    def measures(self, perm):
        ms = self.sim.ms_per_char(perm, self.sc)
        weak = 100.0 * float(self.u @ WEAK[perm]) / self.u_sum
        home = 100.0 * float(self.u @ HOME[perm]) / self.u_sum
        sciss = 100.0 * float((self.W * SCISSOR[np.ix_(perm, perm)]).sum()) / self.W_sum
        f = SLOT_FINGER[perm]
        redir = 100.0 * float(REDIRECT[f[self.ta], f[self.tb], f[self.tc]] @ self.tn) / self.tri_sum
        return ms, weak, home, sciss, redir


def make_obj(C: Constrained, weak_max, home_min, sciss_max, redir_max):
    def obj(perm):
        ms, weak, home, sciss, redir = C.measures(perm)
        pen = 0.0
        if weak > weak_max:
            pen += 2.0 * (weak - weak_max) ** 2
        if home < home_min:
            pen += 2.0 * (home_min - home) ** 2
        if sciss > sciss_max:
            pen += 60.0 * (sciss - sciss_max) ** 2
        if redir > redir_max:
            pen += 8.0 * (redir - redir_max) ** 2
        return ms + pen
    return obj


def anneal(obj, seed, iters=260_000, t0=8.0, t1=0.008):
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
                best, bperm = c, perm.copy()
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


def main():
    profile = sys.argv[1] if len(sys.argv) > 1 else "dev-at"
    restarts = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    iters = int(sys.argv[3]) if len(sys.argv) > 3 else 260_000

    base = data.base_corpora()
    train, test = data.mixes(base, profile)
    C = Constrained(train, simfast.SimCorpus(train))
    C_test = Constrained(test, simfast.SimCorpus(test))

    ref = {}
    print(f"{'layout':<10}{'ms/char':>9}{'weak%':>8}{'home%':>8}{'sciss%':>9}{'redir%':>9}")
    print("-" * 53)
    for n in ("QWERTZ", "Neo2", "Bone", "KOY", "AdNW", "AdNWzjßf"):
        p = simfast.mapping_to_perm(layouts.to_mapping(n))
        m = C.measures(p)
        ref[n] = m
        print(f"{n:<10}{m[0]:>9.3f}{m[1]:>8.1f}{m[2]:>8.1f}{m[3]:>9.2f}{m[4]:>9.2f}")

    a_ms, a_weak, a_home, a_sciss, a_redir = ref["AdNW"]
    print(f"\nConstraint box = AdNW's own comfort figures, with weak-finger load capped")
    print(f"progressively lower. Time must also come in at or under AdNW's {a_ms:.3f} ms/char.\n")

    print(f"{'weak cap':>9}{'ms/char':>10}{'weak%':>8}{'home%':>8}{'sciss%':>9}{'redir%':>9}"
          f"{'feasible':>10}   layout")
    print("-" * 118)
    results = []
    for cap in (41.0, 38.0, 35.0, 32.0, 30.0, 28.0):
        obj = make_obj(C, cap, a_home, a_sciss, a_redir)
        best, bv = None, float("inf")
        for s in range(restarts):
            p, v = anneal(obj, seed=31000 + int(cap) * 11 + s, iters=iters)
            p, v = polish(p, obj)
            if v < bv:
                best, bv = p, v
        ms, weak, home, sciss, redir = C.measures(best)
        ok = (weak <= cap + 0.35 and home >= a_home - 0.35
              and sciss <= a_sciss + 0.03 and redir <= a_redir + 0.15 and ms <= a_ms + 0.02)
        s_out = simfast.perm_to_string(best)
        results.append((cap, ms, weak, home, sciss, redir, ok, s_out))
        print(f"{cap:>9.0f}{ms:>10.3f}{weak:>8.1f}{home:>8.1f}{sciss:>9.2f}{redir:>9.2f}"
              f"{'YES' if ok else 'no':>10}   {s_out}", flush=True)

    tab, nl = chr(9), chr(10)
    with open(f"constrained_frontier_{profile}.tsv", "w", encoding="utf-8") as fh:
        cols = ["cap", "ms_train", "weak_train", "home", "sciss", "redir", "feasible", "layout"]
        fh.write(tab.join(cols) + nl)
        for cap, ms, weak, home, sciss, redir, ok, s_out in results:
            fh.write(tab.join([f"{cap:.0f}", f"{ms:.3f}", f"{weak:.1f}", f"{home:.1f}",
                               f"{sciss:.2f}", f"{redir:.2f}",
                               "YES" if ok else "no", s_out]) + nl)

    feasible = [r for r in results if r[6]]
    if feasible:
        pick = min(feasible, key=lambda r: r[2])       # lowest weak-finger load that works
        print(f"\nTightest feasible point: weak load {pick[2]:.1f}% "
              f"(AdNW {a_weak:.1f}%), at {pick[1]:.3f} ms/char (AdNW {a_ms:.3f}).")
        print(layouts.render(pick[7], "ZEHN"))
        print(f"string: {pick[7]}")
        with open(f"result_final_{profile}.txt", "w", encoding="utf-8") as f:
            f.write(pick[7] + "\n")

        print("\nHeld-out check on the same layout:")
        mt = C_test.measures(simfast.mapping_to_perm(layouts.to_mapping("Z", pick[7])))
        at = C_test.measures(simfast.mapping_to_perm(layouts.to_mapping("AdNW")))
        print(f"{'':<10}{'ms/char':>9}{'weak%':>8}{'home%':>8}{'sciss%':>9}{'redir%':>9}")
        print(f"{'ZEHN':<10}{mt[0]:>9.3f}{mt[1]:>8.1f}{mt[2]:>8.1f}{mt[3]:>9.2f}{mt[4]:>9.2f}")
        print(f"{'AdNW':<10}{at[0]:>9.3f}{at[1]:>8.1f}{at[2]:>8.1f}{at[3]:>9.2f}{at[4]:>9.2f}")
    else:
        print("\nNo feasible point found. AdNW is at or near the achievable frontier and")
        print("the honest recommendation is to use it rather than anything invented here.")


if __name__ == "__main__":
    main()
