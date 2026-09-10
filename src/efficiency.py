"""Efficiency measured with as few invented numbers as possible.

Three levels of assumption, reported separately so you can see which conclusions depend
on what:

  LEVEL 0 -- no parameters at all.
     How far do the fingers actually move to type a text, and how is the work spread
     across them. Pure geometry and corpus counts. Nothing here can be tuned to favour a
     layout.

     Finger travel is bracketed rather than assumed, because how much a hand drifts back
     toward home between presses is not knowable from first principles:
        HOVER  - a finger stays where it last pressed (skilled, minimal-motion typing)
        RETURN - a finger returns home after every press (textbook technique)
     The truth is in between. If a layout wins under both bounds, the ranking is safe.

  LEVEL 1 -- three physical time constants, swept.
     The parallel-finger simulator. Rather than pick values, sweep the plausible range
     and report whether the ranking ever changes.

  LEVEL 2 -- the hand-weighted effort model in metrics.py, shown for comparison only.
     This is the one that encodes my opinions. It is not used to draw conclusions here.
"""

from __future__ import annotations

import sys

import numpy as np

import corpora
import data
import layouts
import simfast
from keyboard import KEYS, SPACE, TH, dist, home_key, travel_from_home
from simulate import Simulator, sample_text

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------------
# LEVEL 0: parameter-free
# ---------------------------------------------------------------------------------
def travel_hover(mapping: dict[str, str], text: str) -> float:
    """mm of finger movement per character, fingers staying where they last pressed."""
    key = {c: KEYS[s] for c, s in mapping.items()}
    key[" "] = SPACE
    pos: dict[int, object] = {}
    total = 0.0
    n = 0
    for ch in text:
        k = key.get(ch)
        if k is None:
            continue
        n += 1
        if k.finger == TH:
            continue
        p = pos.get(k.finger)
        total += dist(p, k) if p is not None else dist(home_key(k.finger), k)
        pos[k.finger] = k
    return total / max(n, 1)


def travel_return(mapping: dict[str, str], ng) -> float:
    """mm per character if every finger returns to its home key after each press."""
    total = 0.0
    for c, count in ng.unigrams.items():
        total += 2.0 * travel_from_home(KEYS[mapping[c]]) * count
    return total / ng.total


def collisions(mapping: dict[str, str], ng) -> tuple[float, float]:
    """Same-finger reuse: rate at lag 1, and mm of forced serial travel per character.

    'Forced serial travel' is the movement a finger must make between two keystrokes
    that are close together in time, which is the movement that cannot hide behind the
    other hand. Counted over lags 1-4 with no weighting beyond the corpus itself.
    """
    key = {c: KEYS[s] for c, s in mapping.items()}
    lag1 = 0.0
    lag1_total = sum(ng.lags[1].values())
    forced = 0.0
    for lag in range(1, simfast.MAX_LAG + 1):
        for (a, b), n in ng.lags[lag].items():
            ka, kb = key[a], key[b]
            if ka.finger == kb.finger and a != b:
                d = dist(ka, kb)
                forced += d * n
                if lag == 1:
                    lag1 += n
    return (100.0 * lag1 / lag1_total if lag1_total else 0.0, forced / ng.total)


def load_spread(mapping: dict[str, str], ng) -> tuple[float, float, float]:
    load = np.zeros(8)
    for c, n in ng.unigrams.items():
        f = KEYS[mapping[c]].finger
        if f != TH:
            load[f] += n
    share = 100.0 * load / load.sum()
    weak = share[0] + share[1] + share[6] + share[7]      # pinkies and ring fingers
    imbalance = abs(share[:4].sum() - 50.0)
    return share.max(), weak, imbalance


# ---------------------------------------------------------------------------------
# LEVEL 1: swept simulator
# ---------------------------------------------------------------------------------
def sweep(entries, sc) -> dict[str, list[float]]:
    """ms/char for each layout across a grid of physical parameters."""
    grid = []
    for gap in (30.0, 46.0, 62.0, 80.0):
        for dwell in (24.0, 32.0, 45.0):
            for speed, tmove in ((2.4, 30.0), (3.1, 38.0), (4.2, 50.0)):
                grid.append((gap, dwell, speed, tmove))
    out = {name: [] for name, _ in entries}
    for gap, dwell, speed, tmove in grid:
        sim = simfast.SimScorer(dwell=dwell, gap=gap, t_move=tmove, speed=speed)
        for name, mapping in entries:
            out[name].append(sim.ms_per_char(simfast.mapping_to_perm(mapping), sc))
    return out


def main() -> None:
    profile = sys.argv[1] if len(sys.argv) > 1 else "dev-at"
    base = data.base_corpora()
    _, test = data.mixes(base, profile)

    entries = [(n, layouts.to_mapping(n)) for n in layouts.ALL]
    for fname, label in ((f"result_final_{profile}.txt", "ZEHN"),
                         (f"result_{profile}.txt", "ZEHN-w"),
                         (f"result_sim_{profile}.txt", "MECH")):
        try:
            s = open(fname, encoding="utf-8").readline().strip()
            entries.append((label, layouts.to_mapping(label, s)))
        except (OSError, IndexError):
            pass

    hover_text = sample_text("corpus/de_test", 300_000)

    print("=" * 100)
    print("LEVEL 0 -- no tunable parameters. Geometry and corpus counts only.")
    print("=" * 100)
    hdr = (f"{'layout':<12}{'travel HOVER':>14}{'travel RETURN':>15}"
           f"{'same-finger%':>14}{'forced mm/ch':>14}{'busiest%':>10}{'weak%':>8}{'imbal':>7}")
    print(hdr)
    print("-" * len(hdr))
    rows = []
    for name, mapping in entries:
        th = travel_hover(mapping, hover_text)
        tr = travel_return(mapping, test)
        sf, forced = collisions(mapping, test)
        busiest, weak, imbal = load_spread(mapping, test)
        rows.append((th, name, tr, sf, forced, busiest, weak, imbal))
    for th, name, tr, sf, forced, busiest, weak, imbal in sorted(rows):
        print(f"{name:<12}{th:>14.2f}{tr:>15.2f}{sf:>14.2f}{forced:>14.3f}"
              f"{busiest:>10.1f}{weak:>8.1f}{imbal:>7.1f}")

    print("\n(HOVER and RETURN bracket the truth. A layout that wins under both is)")
    print("(genuinely moving your fingers less, under any assumption about hand drift.)")

    print("\n" + "=" * 100)
    print("LEVEL 1 -- parallel-finger simulator, swept over 36 parameter combinations")
    print("=" * 100)
    sc = simfast.SimCorpus(test)
    sw = sweep(entries, sc)
    names = [n for n, _ in entries]
    mean_rank = {}
    wins = {n: 0 for n in names}
    for i in range(len(next(iter(sw.values())))):
        order = sorted(names, key=lambda n: sw[n][i])
        wins[order[0]] += 1
        for r, n in enumerate(order):
            mean_rank.setdefault(n, []).append(r + 1)
    n_settings = len(next(iter(sw.values())))
    print(f"{'layout':<12}{'best ms/ch':>12}{'worst ms/ch':>13}{'mean rank':>11}"
          f"{'times 1st':>11}")
    print("-" * 59)
    for n in sorted(names, key=lambda n: np.mean(mean_rank[n])):
        print(f"{n:<12}{min(sw[n]):>12.2f}{max(sw[n]):>13.2f}"
              f"{np.mean(mean_rank[n]):>11.2f}{wins[n]:>8}/{n_settings}")

    q = np.array(sw["QWERTZ"])
    for target in ("ZEHN", "ZEHN-SIM", "AdNW"):
        if target in sw:
            g = 100.0 * (q - np.array(sw[target])) / q
            print(f"\n{target} vs QWERTZ across the sweep: "
                  f"{g.min():.1f}% to {g.max():.1f}% faster (mean {g.mean():.1f}%)")

    print("\nNote the size of that range. How much a layout is worth depends strongly on")
    print("how fast you already type: at a slow sequencing rate the fingers always have")
    print("time to arrive and the layout barely matters, while at speed the same-finger")
    print("collisions become the binding constraint. Anyone quoting a single percentage")
    print("for a layout's benefit is hiding this.")


if __name__ == "__main__":
    main()
