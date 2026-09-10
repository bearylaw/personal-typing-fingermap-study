"""The finger map for a standard German/Austrian ISO keyboard (QWERTZ, T1).

Which finger presses which key, drawn on the real 105-key geometry including the number
row, the modifiers and the ISO extra key. Colour is a per-hand ramp ordered pinky -> index,
and every key also carries its finger label, so nothing depends on colour alone.

Also emits the reach distances that make some of these assignments uncomfortable, and the
two habit changes the rest of this study found to be worth the most on QWERTZ specifically.
"""

from __future__ import annotations

import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from keyboard import KEYS, PITCH, home_key, travel_from_home

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#8a8984"

# Per-hand sequential ramps, ordered pinky (dark) -> index (light).
LEFT_RAMP = {0: "#17416f", 1: "#2a78d6", 2: "#79ade8", 3: "#bcd6f4"}
RIGHT_RAMP = {7: "#8c3a14", 6: "#eb6834", 5: "#f4a077", 4: "#fac9ae"}
THUMB = "#c9c8c1"
BLANK = "#eceae4"

RAMP = {**LEFT_RAMP, **RIGHT_RAMP}
LABEL = {0: "LP", 1: "LR", 2: "LM", 3: "LI", 4: "RI", 5: "RM", 6: "RR", 7: "RP", 8: "TH"}
DARK_KEYS = {0, 7, 1, 6}          # keys whose fill is dark enough to need white text

# The full board. (label, width in units, finger or None)
ROWS = [
    (0.00, [("^", 1, 0), ("1", 1, 0), ("2", 1, 1), ("3", 1, 2), ("4", 1, 3), ("5", 1, 3),
            ("6", 1, 4), ("7", 1, 4), ("8", 1, 5), ("9", 1, 6), ("0", 1, 7),
            ("ß", 1, 7), ("´", 1, 7), ("⌫ Back", 2, 7)]),
    (0.00, [("⇥ Tab", 1.5, 0), ("Q", 1, 0), ("W", 1, 1), ("E", 1, 2), ("R", 1, 3),
            ("T", 1, 3), ("Z", 1, 4), ("U", 1, 4), ("I", 1, 5), ("O", 1, 6), ("P", 1, 7),
            ("Ü", 1, 7), ("+", 1, 7), ("↵", 1.5, 7)]),
    (0.00, [("⇪ Caps", 1.75, 0), ("A", 1, 0), ("S", 1, 1), ("D", 1, 2), ("F", 1, 3),
            ("G", 1, 3), ("H", 1, 4), ("J", 1, 4), ("K", 1, 5), ("L", 1, 6), ("Ö", 1, 7),
            ("Ä", 1, 7), ("#", 1, 7), ("Enter", 1.25, 7)]),
    (0.00, [("⇧ Shift", 1.25, 0), ("<", 1, 0), ("Y", 1, 0), ("X", 1, 1), ("C", 1, 2),
            ("V", 1, 3), ("B", 1, 3), ("N", 1, 4), ("M", 1, 4), (",", 1, 5), (".", 1, 6),
            ("-", 1, 7), ("⇧ Shift", 2.75, 7)]),
    (0.00, [("Ctrl", 1.25, 0), ("Win", 1.25, 0), ("Alt", 1.25, 8), ("Space", 6.25, 8),
            ("AltGr", 1.25, 8), ("Win", 1.25, 8), ("Menu", 1.25, 7), ("Ctrl", 1.25, 7)]),
]


def draw(path: str = "figures/qwertz_fingermap.png") -> None:
    fig, ax = plt.subplots(figsize=(13.6, 5.2))
    y = 0.0
    for _, keys in ROWS:
        x = 0.0
        for label, w, finger in keys:
            col = BLANK if finger is None else (THUMB if finger == 8 else RAMP[finger])
            ax.add_patch(FancyBboxPatch((x + 0.04, -y + 0.04), w - 0.08, 0.92,
                                        boxstyle="round,pad=0,rounding_size=0.10",
                                        linewidth=1.1, edgecolor="#ffffff", facecolor=col))
            light = finger in DARK_KEYS
            ax.text(x + w / 2, -y + 0.62, label, ha="center", va="center",
                    fontsize=11.5 if len(label) <= 2 else 8.6,
                    color="#ffffff" if light else INK)
            if finger is not None:
                ax.text(x + w / 2, -y + 0.24, LABEL[finger], ha="center", va="center",
                        fontsize=7.2, color="#ffffff" if light else INK2)
            x += w
        y += 1.0

    ax.set_xlim(-0.2, 15.2)
    ax.set_ylim(-4.3, 1.5)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.text(-0.2, 1.28, "German / Austrian QWERTZ (ISO 105) — which finger presses which key",
            fontsize=15, color=INK, ha="left", va="center")

    order = [0, 1, 2, 3, 8, 4, 5, 6, 7]
    names = {0: "left pinky", 1: "left ring", 2: "left middle", 3: "left index",
             8: "thumbs", 4: "right index", 5: "right middle", 6: "right ring",
             7: "right pinky"}
    lx = -0.2
    for f in order:
        col = THUMB if f == 8 else RAMP[f]
        ax.add_patch(FancyBboxPatch((lx, -4.25), 0.34, 0.34,
                                    boxstyle="round,pad=0,rounding_size=0.06",
                                    linewidth=0, facecolor=col))
        ax.text(lx + 0.44, -4.08, f"{LABEL[f]} {names[f]}", fontsize=8.6,
                color=INK2, va="center")
        lx += 1.72

    fig.text(0.012, 0.016,
             "Home position: fingers rest on A S D F  /  J K L Ö. Every finger returns "
             "there. Thumbs cover Space; the right thumb also takes AltGr.",
             fontsize=9, color=MUTED)
    fig.tight_layout()
    fig.savefig(path, dpi=175, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"wrote {path}")


def reach_report() -> None:
    """How far each letter key is from its finger's resting position."""
    print("\nReach from the resting key, in millimetres (the assignment is standard;")
    print("these distances are why some of it feels worse than the rest):\n")
    groups = {
        "left pinky   (rests A)": ["q", "a", "<", "y", "1", "^"],
        "left ring    (rests S)": ["w", "s", "x", "2"],
        "left middle  (rests D)": ["e", "d", "c", "3"],
        "left index   (rests F)": ["r", "t", "f", "g", "v", "b", "4", "5"],
        "right index  (rests J)": ["z", "u", "h", "j", "n", "m", "6", "7"],
        "right middle (rests K)": ["i", "k", ",", "8"],
        "right ring   (rests L)": ["o", "l", ".", "9"],
        "right pinky  (rests Ö)": ["p", "ü", "+", "ö", "ä", "#", "-", "0", "ß_key", "´"],
    }
    worst = []
    for name, slots in groups.items():
        parts = []
        for s in slots:
            if s not in KEYS:
                continue
            d = travel_from_home(KEYS[s])
            disp = "ß" if s == "ß_key" else s
            parts.append(f"{disp}={d:.0f}")
            if d > 28:
                worst.append((d, disp, name.split("(")[0].strip()))
        print(f"  {name}:  " + "  ".join(parts))
    print("\nThe long reaches, worst first:")
    for d, s, finger in sorted(worst, reverse=True):
        print(f"  {s:<3} {d:5.1f} mm   {finger}")




def load_figure(path: str = "figures/qwertz_fingerload.png", profile: str = "dev-at") -> None:
    """How the standard discipline actually distributes the work."""
    import data
    import fingersearch as fsr

    base = data.base_corpora()
    _, test = data.mixes(base, profile)
    cte = fsr.Corpus(test)
    cuts = (fsr.STANDARD_CUTS["top"], fsr.STANDARD_CUTS["home"], fsr.STANDARD_CUTS["bot"])
    amap, rest = fsr.build_assignment(*cuts)
    _, _, share, _ = fsr.evaluate(amap, rest, cte)

    order = [0, 1, 2, 3, 4, 5, 6, 7]
    nl = chr(10)
    labels = [f"left{nl}pinky", f"left{nl}ring", f"left{nl}middle", f"left{nl}index",
              f"right{nl}index", f"right{nl}middle", f"right{nl}ring", f"right{nl}pinky"]
    cols = [RAMP[f] for f in order]

    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    bars = ax.bar(range(8), [share[f] for f in order], color=cols, width=0.66)
    for i, f in enumerate(order):
        ax.text(i, share[f] + 0.5, f"{share[f]:.1f}%", ha="center",
                fontsize=10, color=INK2)
    ax.axhline(12.5, color=MUTED, lw=1, ls=(0, (4, 3)))
    ax.text(7.55, 12.9, "even share", fontsize=8.5, color=MUTED, ha="right")
    ax.set_xticks(range(8), labels, fontsize=9)
    ax.set_ylabel("share of keystrokes (%)")
    ax.set_ylim(0, 25)
    ax.set_title("What the standard discipline actually asks of each finger",
                 fontsize=14, color=INK, pad=14, loc="left")
    fig.text(0.012, 0.015,
             "German/English/code mix, held-out text. The right pinky does one eighth of "
             "the work of the left index, because on QWERTZ its keys are P Ü Ö Ä # - .",
             fontsize=8.8, color=MUTED)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color="#e4e3df", lw=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=175, facecolor=SURFACE)
    plt.close(fig)
    print(f"wrote {path}")

if __name__ == "__main__":
    import pathlib
    pathlib.Path("figures").mkdir(exist_ok=True)
    draw()
    load_figure()
    reach_report()
