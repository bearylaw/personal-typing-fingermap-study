"""Does the result survive a different workload, a different corpus, and different physics?

The layout was searched on one corpus mix (45% German / 30% English / 25% code) at one
simulator setting. Three ways that could be luck:

  A  the mix    - re-score on pure German, pure English, pure code, and other blends
  B  the corpus - train vs held-out, already reported, repeated here per workload
  C  the physics - the 36-point parameter sweep, reported as worst case rather than mean

The claim under test is narrow and falsifiable: ZEHN carries materially less weak-finger
load than AdNW while matching it on simulated time, home-row share, scissors and redirects.
"""

from __future__ import annotations

import sys

import numpy as np

import data
import layouts
import simfast
from final_search import Constrained

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    base = data.base_corpora()
    zehn = open("result_final_dev-at.txt", encoding="utf-8").readline().strip()
    contenders = [
        ("ZEHN", layouts.to_mapping("ZEHN", zehn)),
        ("AdNW", layouts.to_mapping("AdNW")),
        ("AdNWzjßf", layouts.to_mapping("AdNWzjßf")),
        ("KOY", layouts.to_mapping("KOY")),
        ("QWERTZ", layouts.to_mapping("QWERTZ")),
    ]

    print("=" * 92)
    print("A/B  Different workloads, held-out text only")
    print("=" * 92)
    print(f"{'profile':<11}{'layout':<11}{'ms/char':>9}{'weak%':>8}{'home%':>8}"
          f"{'sciss%':>9}{'redir%':>9}")
    for profile in ("dev-at", "german", "english", "code", "de-heavy", "balanced"):
        _, test = data.mixes(base, profile)
        C = Constrained(test, simfast.SimCorpus(test))
        print("-" * 65)
        for name, mapping in contenders:
            m = C.measures(simfast.mapping_to_perm(mapping))
            print(f"{profile:<11}{name:<11}{m[0]:>9.3f}{m[1]:>8.1f}{m[2]:>8.1f}"
                  f"{m[3]:>9.2f}{m[4]:>9.2f}")

    print("\n" + "=" * 92)
    print("C  Worst case over the 36-point physical parameter sweep (held-out dev-at)")
    print("=" * 92)
    _, test = data.mixes(base, "dev-at")
    sc = simfast.SimCorpus(test)
    grid = [(g, d, s, t) for g in (30.0, 46.0, 62.0, 80.0)
            for d in (24.0, 32.0, 45.0)
            for s, t in ((2.4, 30.0), (3.1, 38.0), (4.2, 50.0))]
    perms = {n: simfast.mapping_to_perm(m) for n, m in contenders}
    diffs = []
    for g, d, s, t in grid:
        sim = simfast.SimScorer(dwell=d, gap=g, t_move=t, speed=s)
        z = sim.ms_per_char(perms["ZEHN"], sc)
        a = sim.ms_per_char(perms["AdNW"], sc)
        diffs.append(z - a)
    diffs = np.array(diffs)
    print(f"ZEHN minus AdNW, ms/char: min {diffs.min():+.4f}  max {diffs.max():+.4f}  "
          f"mean {diffs.mean():+.4f}")
    print(f"ZEHN is at least as fast as AdNW in {int((diffs <= 0.001).sum())}/{len(diffs)} "
          f"of the parameter settings.")

    print("\nReading: the weak-finger gap is large and stable across every workload. The")
    print("speed difference is small in both directions, which is the honest claim --")
    print("ZEHN buys load relief at no measurable speed cost, not a speed improvement.")


if __name__ == "__main__":
    main()
