"""The actual test: score every layout on held-out text, under three independent yardsticks.

Usage:  python evaluate.py [profile] [extra_layout_string ...]
"""

from __future__ import annotations

import pathlib
import sys

import data
import layouts
from keyboard import FINGER_NAMES
from metrics import HEADER, Scorer

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_results(profile: str) -> dict[str, str]:
    p = pathlib.Path(f"result_{profile}.txt")
    if not p.exists():
        return {}
    lines = [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    out = {}
    if len(lines) > 0:
        out["ZEHN"] = lines[0]
    if len(lines) > 1:
        out["ZEHN-C"] = lines[1]
    return out


def table(ng, names_and_maps, title: str) -> list:
    print(f"\n### {title}   ({ng.name}, {ng.total:,.0f} chars)")
    print(HEADER)
    print("-" * len(HEADER))
    rows = []
    for name, mapping in names_and_maps:
        r = Scorer(mapping).score(ng, name)
        rows.append(r)
    rows.sort(key=lambda r: r.effort_a)
    for r in rows:
        print(r.row())
    return rows


def main() -> None:
    profile = sys.argv[1] if len(sys.argv) > 1 else "dev-at"
    base = data.base_corpora()
    train, test = data.mixes(base, profile)

    entries = [(n, layouts.to_mapping(n)) for n in layouts.ALL]
    for name, s in load_results(profile).items():
        entries.append((name, layouts.to_mapping(name, s)))
    for i, s in enumerate(sys.argv[2:]):
        entries.append((f"EXTRA{i}", layouts.to_mapping(f"EXTRA{i}", s)))

    print("=" * 118)
    print(f"PROFILE: {profile}   mix = {data.PROFILES[profile]}")
    print("=" * 118)
    print("effortA = Model A biomechanical units per 1000 chars (lower better) - "
          "the optimiser's objective")
    print("wpm_B   = Model B Fitts'-law implied words/min (higher better) - independent model")
    print("SFB/skip/home/mm/alt/... = model-free counts, no tuned parameters")

    table(train, entries, "TRAIN (optimiser saw this)")
    rows = table(test, entries, "TEST (held out)")

    print("\n\n### Per-corpus TEST breakdown (Model A effort/1000, lower better)")
    subs = ["de_test", "en_test", "code_test"]
    print(f"{'layout':<12}" + "".join(f"{s:>14}" for s in subs))
    print("-" * (12 + 14 * len(subs)))
    per = []
    for name, mapping in entries:
        sc = Scorer(mapping)
        vals = [sc.score(base[s], name).effort_a for s in subs]
        per.append((name, vals))
    per.sort(key=lambda kv: sum(kv[1]))
    for name, vals in per:
        print(f"{name:<12}" + "".join(f"{v:>14.1f}" for v in vals))

    print("\n\n### Finger load on TEST (% of keystrokes; even is better, pinkies should be low)")
    hdr = f"{'layout':<12}" + "".join(f"{FINGER_NAMES[f][:7]:>9}" for f in range(8))
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r.layout:<12}" + "".join(f"{r.finger_load[f]:>9.1f}" for f in range(8)))

    # headline comparison
    best = rows[0]
    qz = next(r for r in rows if r.layout == "QWERTZ")
    pub = min((r for r in rows if r.layout not in ("QWERTZ",) and not r.layout.startswith("ZEHN")),
              key=lambda r: r.effort_a)
    print("\n\n### Headline (TEST corpus)")
    print(f"  best overall     : {best.layout}")
    print(f"  vs QWERTZ        : effortA {100 * (best.effort_a - qz.effort_a) / qz.effort_a:+.1f}%   "
          f"SFB {best.sfb:.2f}% vs {qz.sfb:.2f}%   "
          f"travel {100 * (best.travel_mm - qz.travel_mm) / qz.travel_mm:+.1f}%   "
          f"wpm_B {100 * (best.wpm_b - qz.wpm_b) / qz.wpm_b:+.1f}%")
    print(f"  vs best published ({pub.layout}): "
          f"effortA {100 * (best.effort_a - pub.effort_a) / pub.effort_a:+.1f}%   "
          f"SFB {best.sfb:.2f}% vs {pub.sfb:.2f}%   "
          f"travel {100 * (best.travel_mm - pub.travel_mm) / pub.travel_mm:+.1f}%   "
          f"wpm_B {100 * (best.wpm_b - pub.wpm_b) / pub.wpm_b:+.1f}%")


if __name__ == "__main__":
    main()
