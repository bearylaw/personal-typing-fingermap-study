"""Draw a layout as a keyboard, with finger assignment and the symbol layer.

    python show.py                 # the ZEHN result for the default profile
    python show.py QWERTZ AdNW     # named reference layouts
    python show.py <32-char-string>
"""

from __future__ import annotations

import sys

import layouts
from keyboard import KEYS, SLOTS_32, FINGER_NAMES
from symbols import _L3_BOTTOM, _L3_HOME, _L3_TOP

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FINGER_MARK = {0: "p", 1: "r", 2: "m", 3: "i", 4: "I", 5: "M", 6: "R", 7: "P"}


def draw(s: str, name: str) -> str:
    top, home, bottom = s[:11], s[11:22], s[22:]
    lines = [f"  {name}", ""]
    lines.append("   " + "  ".join(top[:5]) + "     " + "  ".join(top[5:]))
    lines.append("    " + "  ".join(home[:5]) + "     " + "  ".join(home[5:]))
    lines.append("     " + "  ".join(bottom[:5]) + "     " + "  ".join(bottom[5:]))
    return "\n".join(lines)


def fingers_line() -> str:
    marks = [FINGER_MARK[KEYS[s].finger] for s in SLOTS_32]
    t, h, b = marks[:11], marks[11:22], marks[22:]
    out = ["  finger assignment (lowercase = left hand)", ""]
    out.append("   " + "  ".join(t[:5]) + "     " + "  ".join(t[5:]))
    out.append("    " + "  ".join(h[:5]) + "     " + "  ".join(h[5:]))
    out.append("     " + "  ".join(b[:5]) + "     " + "  ".join(b[5:]))
    out.append("")
    out.append("   p/P pinky   r/R ring   m/M middle   i/I index")
    return "\n".join(out)


def layer3() -> str:
    out = ["  symbol layer (hold Mod3: CapsLock with the left pinky, or the ä key with",
           "  the right pinky -- use the hand opposite the symbol)", ""]
    for row, indent in ((_L3_TOP, "   "), (_L3_HOME, "    "), (_L3_BOTTOM, "     ")):
        cells = list(row)
        out.append(indent + "  ".join(cells[:5]) + "     " + "  ".join(cells[5:]))
    return "\n".join(out)


def main() -> None:
    args = sys.argv[1:]
    if not args:
        try:
            s = open("result_dev-at.txt", encoding="utf-8").readline().strip()
            args = [s]
        except OSError:
            args = ["QWERTZ"]

    for a in args:
        if a in layouts.RAW:
            print(draw(layouts.RAW[a], a))
        elif len(a) == 32:
            print(draw(a, "ZEHN"))
            print(f"\n  driver string: {a}")
        else:
            print(f"  ? not a layout name or a 32-character string: {a!r}")
            continue
        print()

    print(fingers_line())
    print()
    print(layer3())


if __name__ == "__main__":
    main()
