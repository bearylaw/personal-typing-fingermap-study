"""The half of the problem that letter layouts ignore: punctuation and symbols.

On a German/Austrian keyboard the characters a programmer types constantly are the worst
placed characters on the board. { } [ ] \\ @ ~ | all need AltGr, and AltGr is a
right-hand key, so several of them are same-hand contortions. This measures that cost on
a real code corpus and compares it with the Neo-family layer-3 arrangement.

Modelling: a modified keystroke costs the modifier's own key cost plus the base key,
plus a penalty if modifier and key fall on the same hand (the hand has to hold and reach
at once) and a further penalty if they share a finger (impossible without contortion).
"""

from __future__ import annotations

import collections
import pathlib
import sys
import sysconfig

from keyboard import KEYS, LEFT, RIGHT, PITCH, hand, is_stretch, travel_from_home
from metrics import A_FINGER_COST, A_ROW_PEN, A_STRETCH, A_TRAVEL

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Cost of engaging the modifier itself, and of the interaction with the target key.
MOD_PRESS = {"shift": 0.90, "altgr": 0.35, "mod3": 0.90}   # pinky vs thumb
SAME_FINGER = 6.00        # modifier and key on one finger: needs a re-grip
SAME_HAND_FINGER = 1.60   # a finger of that hand is pinned down while the rest reaches
SAME_HAND_THUMB = 0.90    # thumb anchored: cheaper, but the hand is still committed
CROSS_HAND = 0.00         # the comfortable case, and the reason layer 3 works

# --- German/Austrian QWERTZ (T1) ------------------------------------------------------
# character -> (physical slot, modifier) ; modifier in {None, 'shift', 'altgr'}
QWERTZ_SYM = {
    ",": (",", None), ".": (".", None), "-": ("-", None), "+": ("+", None),
    "#": ("#", None), "<": ("<", None), "^": ("^", None), "´": ("´", None),
    "!": ("1", "shift"), '"': ("2", "shift"), "§": ("3", "shift"), "$": ("4", "shift"),
    "%": ("5", "shift"), "&": ("6", "shift"), "/": ("7", "shift"), "(": ("8", "shift"),
    ")": ("9", "shift"), "=": ("0", "shift"), "?": ("ß_key", "shift"),
    "`": ("´", "shift"), "*": ("+", "shift"), "'": ("#", "shift"),
    ">": ("<", "shift"), ";": (",", "shift"), ":": (".", "shift"), "_": ("-", "shift"),
    "{": ("7", "altgr"), "[": ("8", "altgr"), "]": ("9", "altgr"), "}": ("0", "altgr"),
    "\\": ("ß_key", "altgr"), "~": ("+", "altgr"), "|": ("<", "altgr"),
    "@": ("q", "altgr"), "ß": ("ß_key", None),
}

# --- Neo-family layer 3 ---------------------------------------------------------------
_L3_TOP = "…_[]^!<>=&ſ"
_L3_HOME = "\\/{}*?()-:@"
_L3_BOTTOM = "#$|~`+%\"';"
_SLOTS_TOP = ["q", "w", "e", "r", "t", "z", "u", "i", "o", "p", "ü"]
_SLOTS_HOME = ["a", "s", "d", "f", "g", "h", "j", "k", "l", "ö", "ä"]
_SLOTS_BOTTOM = ["y", "x", "c", "v", "b", "n", "m", ",", ".", "-"]

NEO_SYM: dict[str, tuple[str, str | None]] = {}
for _chars, _slots in ((_L3_TOP, _SLOTS_TOP), (_L3_HOME, _SLOTS_HOME), (_L3_BOTTOM, _SLOTS_BOTTOM)):
    for _c, _s in zip(_chars, _slots):
        NEO_SYM.setdefault(_c, (_s, "mod3"))

# Which hand and which digit each modifier occupies.
#   Shift: either pinky, on the row below home.
#   AltGr: right of the space bar, pressed with the RIGHT THUMB. Right hand only.
#   Mod3 (Neo family): Caps with the left pinky, or the ä key with the right pinky.
MOD_KEY = {
    "shift": {"L": ("finger", "a"), "R": ("finger", "ö")},
    "altgr": {"R": ("thumb", None)},
    "mod3": {"L": ("finger", "a"), "R": ("finger", "ä")},
}


def _base_cost(slot: str) -> float:
    k = KEYS[slot]
    c = A_FINGER_COST[k.finger] * (1.0 + A_TRAVEL * travel_from_home(k) / PITCH)
    c += A_ROW_PEN[k.row]
    if is_stretch(slot):
        c += A_STRETCH
    return c


def cost(slot: str, mod: str | None) -> float:
    """Effort of one modified keystroke, taking the cheaper of the two modifier hands."""
    base = _base_cost(slot)
    if mod is None:
        return base
    k = KEYS[slot]
    kh = hand(k.finger)
    options = []
    for mh, (kind, mslot) in MOD_KEY[mod].items():
        extra = MOD_PRESS[mod]
        if mh == kh:
            if kind == "thumb":
                extra += SAME_HAND_THUMB
            else:
                extra += SAME_HAND_FINGER
                if KEYS[mslot].finger == k.finger:
                    extra += SAME_FINGER
        else:
            extra += CROSS_HAND
        options.append(extra)
    return base + min(options)


def code_symbol_counts(files: int = 900) -> collections.Counter:
    root = pathlib.Path(sysconfig.get_paths()["stdlib"])
    paths = sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)[:files]
    cnt: collections.Counter = collections.Counter()
    for p in paths:
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for ch in txt:
            if ch in QWERTZ_SYM or ch in NEO_SYM:
                cnt[ch] += 1
    return cnt


def main() -> None:
    cnt = code_symbol_counts()
    total = sum(cnt.values())
    print(f"Python stdlib corpus: {total:,} symbol/punctuation keystrokes\n")

    rows = []
    q_tot = n_tot = 0.0
    for ch, n in cnt.most_common():
        q = QWERTZ_SYM.get(ch)
        e = NEO_SYM.get(ch)
        if not q or not e:
            continue
        qc, ec = cost(*q), cost(*e)
        q_tot += qc * n
        n_tot += ec * n
        rows.append((n, ch, q, qc, e, ec))

    print(f"{'char':>5}{'count':>10}{'share':>8}   {'QWERTZ':<22}{'cost':>7}   "
          f"{'Neo layer 3':<16}{'cost':>7}{'delta':>9}")
    print("-" * 96)
    for n, ch, q, qc, e, ec in rows[:22]:
        qs = f"{q[1] or '':<5} {q[0]}"
        es = f"{e[1] or '':<5} {e[0]}"
        print(f"{ch!r:>5}{n:>10,}{100 * n / total:>7.1f}%   {qs:<22}{qc:>7.2f}   "
              f"{es:<16}{ec:>7.2f}{ec - qc:>9.2f}")

    print("-" * 96)
    print(f"{'TOTAL':>5}{total:>10,}{'':>8}   {'':<22}{q_tot / total:>7.2f}   "
          f"{'':<16}{n_tot / total:>7.2f}{(n_tot - q_tot) / total:>9.2f}")
    print(f"\nMean effort per symbol keystroke: QWERTZ {q_tot / total:.2f}, "
          f"Neo layer 3 {n_tot / total:.2f}  "
          f"({100 * (n_tot - q_tot) / q_tot:+.1f}%)")

    worst = sorted(rows, key=lambda r: -(r[3] - r[5]) * r[0])[:6]
    print("\nWhere the QWERTZ symbol layer hurts most (weighted by frequency):")
    for n, ch, q, qc, e, ec in worst:
        print(f"  {ch!r:>4}  {n:>9,} presses  QWERTZ {q[1] or 'plain'}+{q[0]:<6} "
              f"{qc:5.2f}  ->  layer3 {e[0]:<3} {ec:5.2f}")


if __name__ == "__main__":
    main()
