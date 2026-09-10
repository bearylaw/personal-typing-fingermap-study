"""Single-key changes to the standard discipline, each scored on its own.

The full search says the standard German assignment is on the frontier: nothing beats it
on simulated time without spending more finger travel. That is a statement about the
assignment as a whole. It leaves a narrower and more useful question open -- are there
individual keys where a different finger is measurably better, holding everything else
fixed?

Each candidate below moves exactly one key to an adjacent finger and is scored on the
held-out corpus. A change is only worth making if it improves simulated time AND does not
increase finger travel.
"""

from __future__ import annotations

import sys

import data
import fingersearch as fsr
from keyboard import KEYS, dist, home_key

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NAMES = {0: "LP", 1: "LR", 2: "LM", 3: "LI", 4: "RI", 5: "RM", 6: "RR", 7: "RP"}

# (slot, new finger, short rationale)
CANDIDATES = [
    ("b", 4, "b is exactly equidistant from F and J (34.3 mm each)"),
    ("z", 3, "z currently right index; left index is 38.4 mm vs 30.5 mm"),
    ("6", 3, "6 is 44.9 mm from F but 50.6 mm from J"),
    ("<", 1, "the ISO extra key, currently left pinky"),
    ("y", 1, "y currently left pinky, next to an idle-ish ring finger"),
    ("t", 2, "t is a long left-index reach at 23.8 mm"),
    ("-", 6, "the hyphen, currently the barely-used right pinky"),
    ("ü", 6, "ü currently right pinky at 23.8 mm"),
    ("m", 5, "m currently right index; right middle is idle-ish"),
    ("g", 2, "g is a left-index stretch at 19.0 mm inward"),
    ("h", 5, "h is a right-index stretch at 19.0 mm inward"),
]


def main() -> None:
    profile = sys.argv[1] if len(sys.argv) > 1 else "dev-at"
    base = data.base_corpora()
    _, test = data.mixes(base, profile)
    cte = fsr.Corpus(test)

    std_cuts = (fsr.STANDARD_CUTS["top"], fsr.STANDARD_CUTS["home"], fsr.STANDARD_CUTS["bot"])
    amap, rest = fsr.build_assignment(*std_cuts)
    base_ms, base_weak, base_share, base_travel = fsr.evaluate(amap, rest, cte)

    print("=" * 96)
    print("SINGLE-KEY CHANGES TO THE STANDARD DISCIPLINE (held-out corpus)")
    print("=" * 96)
    print(f"standard: {base_ms:.3f} ms/char   {base_travel:.2f} mm/char travel   "
          f"{base_weak:.1f}% weak-finger load\n")
    print(f"{'key':>4} {'from':>5} {'to':>4} {'reach now':>10} {'reach after':>12}"
          f" {'Δ ms/char':>10} {'Δ travel':>10} {'verdict':>9}   why")
    print("-" * 118)

    rows = []
    for slot, new_f, why in CANDIDATES:
        old_f = amap[slot]
        if old_f == new_f:
            continue
        trial = dict(amap)
        trial[slot] = new_f
        # resting keys are unchanged: we are moving one key, not re-seating the hands
        try:
            ms, weak, share, travel = fsr.evaluate(trial, rest, cte)
        except KeyError:
            continue
        d_ms = ms - base_ms
        d_tr = travel - base_travel
        reach_now = dist(KEYS[slot], KEYS[rest[old_f]])
        reach_new = dist(KEYS[slot], KEYS[rest[new_f]])
        good = d_ms < -0.005 and d_tr <= 0.02
        rows.append((d_ms, slot, old_f, new_f, reach_now, reach_new, d_ms, d_tr, good, why))

    for _, slot, old_f, new_f, rn, ra, d_ms, d_tr, good, why in sorted(rows):
        disp = "ß" if slot == "ß_key" else slot
        print(f"{disp:>4} {NAMES[old_f]:>5} {NAMES[new_f]:>4} {rn:>9.1f}mm {ra:>11.1f}mm"
              f" {d_ms:>+10.3f} {d_tr:>+10.2f} {'KEEP' if good else 'no':>9}   {why}")

    print("\nload on the standard discipline, for reference:")
    print("  " + "   ".join(f"{NAMES[f]} {base_share[f]:.1f}%" for f in range(8)))
    keep = [r for r in rows if r[8]]
    print(f"\n{len(keep)} of {len(rows)} candidate changes improve time without costing travel.")
    for _, slot, old_f, new_f, *_ in sorted(keep):
        disp = "ß" if slot == "ß_key" else slot
        print(f"  move {disp!r} from {NAMES[old_f]} to {NAMES[new_f]}")


if __name__ == "__main__":
    main()
