"""Does the ISO angle mod help on a German/Austrian board?

Row stagger pushes the left bottom row to the right of where the left hand naturally
falls, so the left index reaches down-and-in for v/b while the pinky curls under for y.
On an ISO board the extra key left of Y lets the whole left bottom row shift one position
left, straightening the hand. The key is already there and otherwise wasted.

This is a change to finger discipline, not to letters, so it applies to any layout --
including QWERTZ, where it costs nothing to learn beyond the habit itself.
"""

from __future__ import annotations

import sys

import data
import fastscore as fs
import keyboard as kb
import layouts
from metrics import Scorer

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def score_all(ng, names_and_strings):
    out = {}
    for name, s in names_and_strings:
        m = layouts.to_mapping(name, s) if s else layouts.to_mapping(name)
        out[name] = Scorer(m).score(ng, name)
    return out


def main() -> None:
    profile = sys.argv[1] if len(sys.argv) > 1 else "dev-at"
    base = data.base_corpora()
    _, test = data.mixes(base, profile)

    entries = [(n, None) for n in layouts.ALL]
    try:
        lines = [l.strip() for l in open(f"result_{profile}.txt", encoding="utf-8") if l.strip()]
        entries.append(("ZEHN", lines[0]))
        if len(lines) > 1:
            entries.append(("ZEHN-C", lines[1]))
    except OSError:
        pass

    kb.set_variant("standard")
    fs.rebuild()
    std = score_all(test, entries)

    kb.set_variant("angle")
    fs.rebuild()
    ang = score_all(test, entries)

    kb.set_variant("standard")
    fs.rebuild()

    print(f"ISO angle mod, held-out corpus ({test.name})")
    print("Left bottom row shifts one key left onto the '<' key; fingers keep their columns.\n")
    hdr = (f"{'layout':<12}{'effortA std':>13}{'angle':>10}{'delta':>9}"
           f"{'SFB std':>10}{'angle':>8}{'mm/1k std':>12}{'angle':>10}")
    print(hdr)
    print("-" * len(hdr))
    rows = sorted(std, key=lambda n: std[n].effort_a)
    for n in rows:
        a, b = std[n], ang[n]
        print(f"{n:<12}{a.effort_a:>13.1f}{b.effort_a:>10.1f}"
              f"{100 * (b.effort_a - a.effort_a) / a.effort_a:>8.1f}%"
              f"{a.sfb:>10.2f}{b.sfb:>8.2f}{a.travel_mm:>12.0f}{b.travel_mm:>10.0f}")

    gains = [(std[n].effort_a - ang[n].effort_a) / std[n].effort_a for n in std]
    print(f"\nmean change: {100 * sum(gains) / len(gains):+.2f}%   "
          f"helps {sum(1 for g in gains if g > 0)}/{len(gains)} layouts")
    print("\nNote: for QWERTZ this is the cheapest possible ergonomic change -- no new")
    print("letter positions, no driver, just moving four fingers one key to the left.")


if __name__ == "__main__":
    main()
