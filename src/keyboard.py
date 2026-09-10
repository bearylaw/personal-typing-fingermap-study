"""Physical model of a German/Austrian ISO 105-key keyboard, plus finger assignment.

Everything downstream depends on this file being geometrically honest, so the numbers
here are real key positions in millimetres, not abstract grid indices.

Coordinate system: x to the right, y downward, origin at the top-left corner of the
number row. Units are millimetres; one key pitch is 19.05 mm (standard 0.75").

ISO row stagger (offset of the first key in each row, in key units):
    number row  0.00   ^ 1 2 3 4 5 6 7 8 9 0 ß ´
    top row     1.50   (Tab 1.5u)   q w e r t z u i o p ü +
    home row    1.75   (Caps 1.75u) a s d f g h j k l ö ä #
    bottom row  1.25   (LShift 1.25u) < y x c v b n m , . -
"""

from __future__ import annotations

import math
from dataclasses import dataclass

PITCH = 19.05  # mm between key centres

# --------------------------------------------------------------------------------------
# Fingers
# --------------------------------------------------------------------------------------
LP, LR, LM, LI, RI, RM, RR, RP, TH = range(9)
FINGER_NAMES = {
    LP: "L-pinky", LR: "L-ring", LM: "L-mid", LI: "L-index",
    RI: "R-index", RM: "R-mid", RR: "R-ring", RP: "R-pinky", TH: "thumb",
}
LEFT = {LP, LR, LM, LI}
RIGHT = {RI, RM, RR, RP}


def hand(f: int) -> str:
    if f in LEFT:
        return "L"
    if f in RIGHT:
        return "R"
    return "T"


# Position of a finger within its hand, 1 = index ... 4 = pinky.
# Used for roll direction and scissor detection.
FINGER_RANK = {LI: 1, LM: 2, LR: 3, LP: 4, RI: 1, RM: 2, RR: 3, RP: 4}

# --------------------------------------------------------------------------------------
# Physical key positions
# --------------------------------------------------------------------------------------
# row -> (y index, x offset in units, key names left to right)
_ROWS = {
    1: (0, 0.00, ["^", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "ß_key", "´"]),
    2: (1, 1.50, ["q", "w", "e", "r", "t", "z", "u", "i", "o", "p", "ü", "+"]),
    3: (2, 1.75, ["a", "s", "d", "f", "g", "h", "j", "k", "l", "ö", "ä", "#"]),
    4: (3, 1.25, ["<", "y", "x", "c", "v", "b", "n", "m", ",", ".", "-"]),
}

# Standard German 10-finger assignment, by physical slot name.
_FINGER_OF_SLOT = {
    # number row
    "^": LP, "1": LP, "2": LR, "3": LM, "4": LI, "5": LI, "6": RI, "7": RI,
    "8": RM, "9": RR, "0": RP, "ß_key": RP, "´": RP,
    # top row
    "q": LP, "w": LR, "e": LM, "r": LI, "t": LI, "z": RI, "u": RI, "i": RM,
    "o": RR, "p": RP, "ü": RP, "+": RP,
    # home row
    "a": LP, "s": LR, "d": LM, "f": LI, "g": LI, "h": RI, "j": RI, "k": RM,
    "l": RR, "ö": RP, "ä": RP, "#": RP,
    # bottom row
    "<": LP, "y": LP, "x": LR, "c": LM, "v": LI, "b": LI, "n": RI, "m": RI,
    ",": RM, ".": RR, "-": RP,
}

# Where each finger rests.
HOME_SLOT = {LP: "a", LR: "s", LM: "d", LI: "f", RI: "j", RM: "k", RR: "l", RP: "ö"}


@dataclass(frozen=True)
class Key:
    slot: str          # physical slot name (its QWERTZ legend)
    row: int           # 1..4
    col: int           # index within the row, 0-based
    x: float           # centre, mm
    y: float           # centre, mm
    finger: int


def _build_keys() -> dict[str, Key]:
    keys: dict[str, Key] = {}
    for row, (yi, xoff, names) in _ROWS.items():
        for col, name in enumerate(names):
            x = (xoff + col + 0.5) * PITCH
            y = (yi + 0.5) * PITCH
            keys[name] = Key(name, row, col, x, y, _FINGER_OF_SLOT[name])
    return keys


KEYS: dict[str, Key] = _build_keys()

# Thumb / space: modelled as a single key reachable by either thumb.
SPACE = Key("space", 5, 0, 6.0 * PITCH, 4.5 * PITCH, TH)


def home_key(f: int) -> Key:
    return KEYS[HOME_SLOT[f]]


def dist(a: Key, b: Key) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def travel_from_home(k: Key) -> float:
    """How far the finger must leave its resting position, in mm."""
    if k.finger == TH:
        return 0.0
    return dist(k, home_key(k.finger))


# --------------------------------------------------------------------------------------
# The 32 optimisable slots
# --------------------------------------------------------------------------------------
# This is exactly the slot set the Neo-family drivers use (11 + 11 + 10), which means any
# layout produced here can be loaded verbatim with neo2-llkh's customLayout option.
SLOTS_TOP = ["q", "w", "e", "r", "t", "z", "u", "i", "o", "p", "ü"]
SLOTS_HOME = ["a", "s", "d", "f", "g", "h", "j", "k", "l", "ö", "ä"]
SLOTS_BOTTOM = ["y", "x", "c", "v", "b", "n", "m", ",", ".", "-"]
SLOTS_32 = SLOTS_TOP + SLOTS_HOME + SLOTS_BOTTOM

assert len(SLOTS_32) == 32

# Columns that require a lateral stretch (index finger reaching inward to the
# centre columns, or pinky reaching outward past its own column).
_STRETCH_SLOTS = {
    "t", "g", "b",          # left index reaching inward
    "z", "h", "n",          # right index reaching inward
    "ü", "ä", "-",          # right pinky reaching outward
    "ß_key", "´", "+", "#",
}


def is_stretch(slot: str) -> bool:
    return slot in _STRETCH_SLOTS


def finger_of(slot: str) -> int:
    return KEYS[slot].finger


# --------------------------------------------------------------------------------------
# Variant: the ISO angle mod
# --------------------------------------------------------------------------------------
# A row-staggered board pushes the left bottom row to the right of where the left hand
# naturally falls, so the left index has to reach down-and-in for 'v'/'b' while the pinky
# curls under for 'y'. On an ISO board the extra '<' key lets the whole left bottom row
# shift one position left, which straightens the hand. This is the standard "angle mod"
# and it is free on ISO: the key is already there and is otherwise wasted.
#
# It is a change to the *finger discipline*, not to the letters, so it is tested
# separately from the layout search.

VARIANT = "standard"


def set_variant(name: str) -> None:
    """'standard' or 'angle'. Rebuilds KEYS and the bottom-row slot list in place."""
    global VARIANT
    if name not in ("standard", "angle"):
        raise ValueError(name)
    VARIANT = name
    if name == "standard":
        _FINGER_OF_SLOT.update({"<": LP, "y": LP, "x": LR, "c": LM, "v": LI, "b": LI})
        bottom = ["y", "x", "c", "v", "b", "n", "m", ",", ".", "-"]
    else:
        # left bottom row shifts one key left onto '<'; 'b' leaves the optimisable set
        # because nothing should live on that reach.
        _FINGER_OF_SLOT.update({"<": LP, "y": LR, "x": LM, "c": LI, "v": LI, "b": LI})
        bottom = ["<", "y", "x", "c", "v", "n", "m", ",", ".", "-"]
    # mutate in place: other modules hold references to these objects
    SLOTS_BOTTOM[:] = bottom
    SLOTS_32[:] = SLOTS_TOP + SLOTS_HOME + SLOTS_BOTTOM
    KEYS.clear()
    KEYS.update(_build_keys())
    assert len(SLOTS_32) == 32


def describe() -> str:
    out = ["Physical model: ISO 105-key, German/Austrian (T1), pitch 19.05 mm", ""]
    for row, (_, _, names) in _ROWS.items():
        cells = []
        for n in names:
            k = KEYS[n]
            cells.append(f"{n:>5}:{FINGER_NAMES[k.finger][:7]:<7}")
        out.append(f"row {row}: " + " ".join(cells))
    return "\n".join(out)


if __name__ == "__main__":
    print(describe())
    print()
    print("Travel from home (mm) for the 32 optimisable slots:")
    for label, slots in (("top", SLOTS_TOP), ("home", SLOTS_HOME), ("bottom", SLOTS_BOTTOM)):
        vals = " ".join(f"{s}={travel_from_home(KEYS[s]):4.1f}" for s in slots)
        print(f"  {label:<7}{vals}")
