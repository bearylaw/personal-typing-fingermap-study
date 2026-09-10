"""Reference layouts.

The Neo-family strings are taken verbatim from the neo2-llkh driver source
(src/main.c, MaxGyver83/neo2-llkh), which is the authoritative machine-readable
definition rather than a picture of a keyboard. Format is 11 + 11 + 10 = 32 characters
filling the slots q..ü / a..ä / y..- .
"""

from __future__ import annotations

from keyboard import SLOTS_32

# name -> 32-character string (top 11, home 11, bottom 10)
RAW: dict[str, str] = {
    # The baseline: what the user types on today.
    "QWERTZ":   "qwertzuiopü" "asdfghjklöä" "yxcvbnm,.-",
    # Neo family, German-optimised.
    "Neo2":     "xvlcwkhgfqß" "uiaeosnrtdy" "üöäpzbm,.j",
    "Bone":     "jduaxphlmwß" "ctieobnrsgq" "fvüäöyz,.k",
    "AdNW":     "kuü.ävgcljf" "hieaodtrnsß" "xyö,qbpwmz",
    "AdNWzjßf": "kuü.ävgclßz" "hieaodtrnsf" "xyö,qbpwmj",
    "KOY":      "k.o,yvgclßz" "haeiudtrnsf" "xqäüöbpwmj",
    "KOU":      "k.ouäqgclfj" "haeiybtrnsß" "zx,üöpdwmv",
    "VOU":      "v.ouäqglhfj" "caeiybtrnsß" "zx,üöpdwmk",
}

# QWERTZ is the odd one out: it has no ß in the main block (ß sits on the number row)
# and spends a main-block slot on '-' instead. Handled explicitly so the comparison is
# geometrically honest rather than quietly dropping a character.
SPECIAL_SLOT = {
    "QWERTZ": {"ß": "ß_key"},
}


def to_mapping(name: str, s: str | None = None) -> dict[str, str]:
    """Return {character: physical slot}. Raises if the layout is malformed."""
    s = RAW[name] if s is None else s
    if len(s) != 32:
        raise ValueError(f"{name}: expected 32 characters, got {len(s)}")
    mapping = {ch: slot for ch, slot in zip(s, SLOTS_32)}
    if len(mapping) != 32:
        dupes = [c for c in set(s) if s.count(c) > 1]
        raise ValueError(f"{name}: duplicate characters {dupes}")
    for ch, slot in SPECIAL_SLOT.get(name, {}).items():
        mapping[ch] = slot
    return mapping


def render(s: str, name: str = "") -> str:
    top, home, bottom = s[:11], s[11:22], s[22:]
    pad = lambda row: " ".join(row)
    lines = []
    if name:
        lines.append(name)
    lines.append("    " + pad(top))
    lines.append("     " + pad(home))
    lines.append("      " + pad(bottom))
    return "\n".join(lines)


ALL = list(RAW)


def validate_all() -> None:
    for n in ALL:
        m = to_mapping(n)
        missing = set("abcdefghijklmnopqrstuvwxyzäöüß,.") - set(m)
        if missing:
            raise ValueError(f"{n}: missing characters {sorted(missing)}")


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    validate_all()
    for n in ALL:
        print(render(RAW[n], n))
        print()
    print("all layouts valid: every one covers a-z, ä, ö, ü, ß, comma, period")
