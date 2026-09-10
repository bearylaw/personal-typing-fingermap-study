"""Does the result survive if the effort model is wrong?

The layout was optimised against one particular set of weights. If small changes to those
weights reshuffle the ranking, the winner is an artefact of my parameter choices rather
than a fact about typing. This perturbs every Model-A weight by up to +/-40%, re-scores
all layouts on the held-out corpus, and reports how often each layout comes first.
"""

from __future__ import annotations

import random
import sys

import numpy as np

import data
import fastscore
import layouts
import metrics
from evaluate import load_results

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TUNABLE = [
    "A_TRAVEL", "A_STRETCH", "A_SFB", "A_SFB_DIST", "A_SKIP", "A_ROWJUMP",
    "A_SCISSOR", "A_ROLL_IN", "A_ROLL_OUT", "A_ALTERNATE", "A_REDIRECT",
    "A_REDIRECT_NOIDX", "A_BALANCE",
]


def perturb(rng: random.Random, spread: float) -> dict:
    saved = {k: getattr(metrics, k) for k in TUNABLE}
    saved["A_FINGER_COST"] = dict(metrics.A_FINGER_COST)
    saved["A_ROW_PEN"] = dict(metrics.A_ROW_PEN)
    for k in TUNABLE:
        setattr(metrics, k, saved[k] * rng.uniform(1 - spread, 1 + spread))
    metrics.A_FINGER_COST = {f: v * rng.uniform(1 - spread, 1 + spread)
                             for f, v in saved["A_FINGER_COST"].items()}
    metrics.A_ROW_PEN = {r: v * rng.uniform(1 - spread, 1 + spread)
                         for r, v in saved["A_ROW_PEN"].items()}
    return saved


def restore(saved: dict) -> None:
    for k, v in saved.items():
        setattr(metrics, k, v)


def main() -> None:
    profile = sys.argv[1] if len(sys.argv) > 1 else "dev-at"
    trials = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    spread = float(sys.argv[3]) if len(sys.argv) > 3 else 0.40

    base = data.base_corpora()
    _, test = data.mixes(base, profile)

    entries = [(n, layouts.to_mapping(n)) for n in layouts.ALL]
    for name, s in load_results(profile).items():
        entries.append((name, layouts.to_mapping(name, s)))

    names = [n for n, _ in entries]
    wins = {n: 0 for n in names}
    top2 = {n: 0 for n in names}
    ranks = {n: [] for n in names}
    rng = random.Random(20260910)

    print(f"perturbing {len(TUNABLE) + 12} Model-A weights by +/-{spread:.0%}, "
          f"{trials} trials, scored on held-out {test.name}")

    for _ in range(trials):
        saved = perturb(rng, spread)
        try:
            scored = sorted(
                ((metrics.Scorer(m).score(test, n).effort_a, n) for n, m in entries)
            )
        finally:
            restore(saved)
        wins[scored[0][1]] += 1
        for i, (_, n) in enumerate(scored):
            ranks[n].append(i + 1)
            if i < 2:
                top2[n] += 1

    print(f"\n{'layout':<12}{'win%':>8}{'top2%':>8}{'mean rank':>11}{'worst rank':>12}")
    print("-" * 51)
    for n in sorted(names, key=lambda n: -wins[n]):
        print(f"{n:<12}{100 * wins[n] / trials:>8.1f}{100 * top2[n] / trials:>8.1f}"
              f"{np.mean(ranks[n]):>11.2f}{max(ranks[n]):>12d}")

    print("\nReading: a layout that wins under almost any reasonable weighting is a real")
    print("finding. One that wins only at my exact weights is a tuning artefact.")


if __name__ == "__main__":
    main()
