"""Two parts of a ten-finger system that layout research usually ignores.

1. Shift discipline. German capitalises every noun, so a German typist presses Shift far
   more often than an English one. Using the Shift on the *same* hand as the letter is a
   pinky contortion; using the opposite one is nearly free. This measures the gap.

2. Backspace. It is one of the most-pressed keys on any keyboard and it sits at the far
   top-right corner, the longest reach the right pinky ever makes. Moving it to a thumb
   costs nothing to learn. This computes the break-even frequency.
"""

from __future__ import annotations

import pathlib
import sys
from collections import Counter

import corpora
import layouts
from keyboard import KEYS, PITCH, TH, hand, is_stretch, travel_from_home
from metrics import A_FINGER_COST, A_ROW_PEN, A_TRAVEL, A_STRETCH
from symbols import MOD_PRESS, SAME_FINGER, SAME_HAND_FINGER, CROSS_HAND

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def base_cost(slot: str) -> float:
    k = KEYS[slot]
    c = A_FINGER_COST[k.finger] * (1.0 + A_TRAVEL * travel_from_home(k) / PITCH)
    c += A_ROW_PEN[k.row]
    if is_stretch(slot):
        c += A_STRETCH
    return c


def uppercase_rates() -> dict[str, tuple[float, Counter]]:
    """Share of alphabetic characters that are capitals, per corpus."""
    out = {}
    for label, path in (("German (Gutenberg)", "corpus/de_train"),
                        ("German (Wikipedia)", None),
                        ("English", "corpus/train")):
        if path is None:
            p = pathlib.Path("corpus/_wiki_de.txt")
            if not p.exists():
                p = pathlib.Path("corpus/_wiki_de_raw.txt")
            text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        else:
            text = corpora.load_dir(path)
        upper = Counter()
        n_alpha = n_upper = 0
        for ch in text:
            if ch.isalpha():
                n_alpha += 1
                if ch.isupper():
                    n_upper += 1
                    upper[ch.lower()] += 1
        out[label] = (100.0 * n_upper / n_alpha if n_alpha else 0.0, upper)
    return out


def shift_costs(layout_name: str, upper: Counter) -> tuple[float, float]:
    """Mean cost of a capital, using the opposite-hand Shift vs the same-hand Shift."""
    mapping = layouts.to_mapping(layout_name)
    tot = sum(upper.values()) or 1
    opp = same = 0.0
    for ch, n in upper.items():
        slot = mapping.get(ch)
        if slot is None:
            continue
        k = KEYS[slot]
        b = base_cost(slot)
        # opposite hand: Shift pinky is free of the reaching hand
        opp += (b + MOD_PRESS["shift"] + CROSS_HAND) * n
        # same hand: that hand's pinky is pinned; if the letter IS on the pinky, worse
        extra = MOD_PRESS["shift"] + SAME_HAND_FINGER
        if k.finger in (0, 7):
            extra += SAME_FINGER
        same += (b + extra) * n
    return opp / tot, same / tot


def main() -> None:
    print("=" * 78)
    print("1. SHIFT DISCIPLINE")
    print("=" * 78)
    rates = uppercase_rates()
    print(f"\n{'corpus':<24}{'capitals as % of letters':>26}")
    for label, (rate, _) in rates.items():
        print(f"{label:<24}{rate:>25.2f}%")

    _, de_upper = rates["German (Gutenberg)"]
    _, en_upper = rates["English"]

    print(f"\n{'layout':<12}{'German: opp':>13}{'same':>9}{'penalty':>10}"
          f"{'English: opp':>15}{'same':>9}{'penalty':>10}")
    print("-" * 78)
    for name in ("QWERTZ", "Neo2", "AdNW", "KOY"):
        do, ds = shift_costs(name, de_upper)
        eo, es = shift_costs(name, en_upper)
        print(f"{name:<12}{do:>13.2f}{ds:>9.2f}{100 * (ds - do) / do:>9.0f}%"
              f"{eo:>15.2f}{es:>9.2f}{100 * (es - eo) / eo:>9.0f}%")

    de_rate = rates["German (Gutenberg)"][0]
    do, ds = shift_costs("QWERTZ", de_upper)
    print(f"\nOn QWERTZ, German text: capitals are {de_rate:.1f}% of letters, and using the")
    print(f"wrong Shift costs {100 * (ds - do) / do:.0f}% more per capital. Over a whole document")
    print(f"that is {de_rate / 100 * (ds - do):.3f} effort units per letter typed -- roughly")
    print(f"{100 * (de_rate / 100 * (ds - do)) / 2.7:.1f}% of total typing effort, for free.")

    print("\n" + "=" * 78)
    print("2. BACKSPACE")
    print("=" * 78)
    # Backspace sits right of the number row: one key further out than ´.
    bs_x = (13 + 0.5) * PITCH
    bs_y = 0.5 * PITCH
    home = KEYS["ö"]
    reach = ((bs_x - home.x) ** 2 + (bs_y - home.y) ** 2) ** 0.5
    bs_cost = A_FINGER_COST[7] * (1.0 + A_TRAVEL * reach / PITCH) + A_ROW_PEN[1] + A_STRETCH
    thumb_cost = 0.35

    print(f"\nBackspace is {reach:.0f} mm from the right pinky's home key -- the longest reach")
    print(f"on the board. Modelled cost {bs_cost:.2f} effort units.")
    print(f"A thumb key (e.g. right Alt remapped) costs about {thumb_cost:.2f}.")
    print(f"Saving per press: {bs_cost - thumb_cost:.2f} units.\n")

    print(f"{'backspace as % of keystrokes':>30}{'effort saved':>15}")
    print("-" * 45)
    for pct in (2.0, 4.0, 5.9, 6.5, 8.0):
        saved = pct / 100 * (bs_cost - thumb_cost)
        print(f"{pct:>29.1f}%{100 * saved / 2.7:>14.1f}%")
    print("\n(Denominator is ~2.7 effort units per character of text, the QWERTZ average,")
    print("so these are savings relative to the cost of typing the text itself.)")
    print("\nDhakal et al., 'Observations on Typing from 136 Million Keystrokes' (CHI 2018)")
    print("measured error-correction rates of 5.9% for trained and 6.5% for untrained")
    print("typists, KSPC 1.173, and found Backspace among the three most-pressed keys")
    print("alongside Space and 'e'. At those rates, moving Backspace to a thumb is worth")
    print("more than the entire letter-layout difference between ZEHN and AdNW -- and it")
    print("requires learning exactly one key.")


if __name__ == "__main__":
    main()
