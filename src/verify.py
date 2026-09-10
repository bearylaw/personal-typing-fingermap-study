"""Sanity checks that must pass before any result is believable.

1. The fast vectorised scorer agrees with the slow readable one.
2. Every layout is a valid permutation of the 32 characters.
3. A deliberately terrible layout scores worse than QWERTZ, and QWERTZ worse than Neo2
   (a sign check: if the model cannot reproduce the known ordering of existing layouts,
   it is not fit to design a new one).
"""

from __future__ import annotations

import random
import sys

import numpy as np

import data
import fastscore as fs
import layouts
from metrics import Scorer

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    base = data.base_corpora()
    train, test = data.mixes(base, "dev-at")
    fc = fs.FastCorpus(train, trigram_coverage=1.0)     # exact, for the equivalence test
    fc_pruned = fs.FastCorpus(train, trigram_coverage=0.995)  # what the optimiser uses

    print(f"corpus units: train={train.total:,.0f} test={test.total:,.0f}")
    print(f"trigrams: {fc.trigram_kept:,} exact / {fc_pruned.trigram_kept:,} pruned "
          f"(99.5% of mass)")
    print()

    ok = True

    # --- 1. fast vs slow ------------------------------------------------------------
    print("1. fast scorer vs reference scorer (Model A, effort/1000 chars)")
    for name in ("Neo2", "Bone", "KOY", "AdNW"):
        mapping = layouts.to_mapping(name)
        slow = Scorer(mapping).score(train, name).effort_a
        fast = fs.effort(fs.mapping_to_perm(mapping), fc)
        delta = abs(slow - fast)
        flag = "ok" if delta < 1e-6 * max(1.0, abs(slow)) else "MISMATCH"
        if flag != "ok":
            ok = False
        print(f"   {name:<10} slow={slow:10.4f}  fast={fast:10.4f}  diff={delta:.2e}  {flag}")

    # random permutations, to catch cases the real layouts happen not to exercise
    rng = random.Random(7)
    worst = 0.0
    for _ in range(40):
        perm = list(range(32))
        rng.shuffle(perm)
        s = fs.perm_to_string(np.array(perm))
        mapping = layouts.to_mapping("_rand", s)
        slow = Scorer(mapping).score(train, "_").effort_a
        fast = fs.effort(np.array(perm), fc)
        worst = max(worst, abs(slow - fast) / max(1.0, abs(slow)))
    print(f"   40 random layouts: worst relative difference {worst:.2e} "
          f"{'ok' if worst < 1e-9 else 'MISMATCH'}")
    if worst >= 1e-9:
        ok = False

    # How much does trigram pruning cost the optimiser's view of the world? It must be
    # small *and* it must not reorder layouts, or the search is chasing an artefact.
    exact, approx = [], []
    for name in layouts.ALL:
        p = fs.mapping_to_perm(layouts.to_mapping(name))
        exact.append(fs.effort(p, fc))
        approx.append(fs.effort(p, fc_pruned))
    err = max(abs(a - b) / a for a, b in zip(exact, approx))
    order_exact = [n for _, n in sorted(zip(exact, layouts.ALL))]
    order_approx = [n for _, n in sorted(zip(approx, layouts.ALL))]
    same_order = order_exact == order_approx
    print(f"   trigram pruning: max relative error {err:.2e}, ranking preserved: {same_order}")
    ok &= same_order and err < 1e-3

    # --- 2. layout validity ---------------------------------------------------------
    print("\n2. reference layouts well-formed")
    layouts.validate_all()
    print("   all 8 layouts cover a-z ä ö ü ß , . exactly once  ok")

    # --- 3. sign check --------------------------------------------------------------
    print("\n3. sign check on Model A (does it reproduce known orderings?)")
    scores = {}
    for name in layouts.ALL:
        scores[name] = Scorer(layouts.to_mapping(name)).score(train, name).effort_a
    # A pathological layout: put the most frequent German letters on the worst keys.
    awful = "qjyxvöäüpwß" "kzgbcfhmldn" "s,.turaieo"
    scores["AWFUL"] = Scorer(layouts.to_mapping("_awful", awful), ).score(train, "_").effort_a
    for n, v in sorted(scores.items(), key=lambda kv: kv[1]):
        print(f"   {n:<10} {v:9.2f}")
    checks = [
        ("Neo2 better than QWERTZ", scores["Neo2"] < scores["QWERTZ"]),
        ("KOY better than QWERTZ", scores["KOY"] < scores["QWERTZ"]),
        ("Bone better than QWERTZ", scores["Bone"] < scores["QWERTZ"]),
        ("QWERTZ better than AWFUL", scores["QWERTZ"] < scores["AWFUL"]),
    ]
    for label, passed in checks:
        print(f"   {'PASS' if passed else 'FAIL'}  {label}")
        ok &= passed

    print("\n" + ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
