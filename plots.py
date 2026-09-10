"""Figures for the write-up. Run after frontier.py and optimize_sim.py.

Palette is the validated three-slot categorical set (all-pairs CVD-safe) plus a single
sequential hue for the keyboard heat maps. Every point that carries meaning is directly
labelled, so identity never depends on colour alone.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

import data
import layouts
import simfast
from efficiency import collisions, load_spread, travel_hover, travel_return
from keyboard import KEYS, SLOTS_32, TH
from simulate import sample_text

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FIG = pathlib.Path("figures")
FIG.mkdir(exist_ok=True)

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#8a8984"
S1 = "#2a78d6"   # blue   - this work
S2 = "#eb6834"   # orange - published alternatives
S3 = "#1baf7a"   # aqua   - QWERTZ baseline
S4 = "#eda100"   # yellow - mechanics-only layout
GRID = "#e4e3df"

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK2,
    "text.color": INK,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
})


def _clean(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def load_frontier(profile="dev-at"):
    p = pathlib.Path(f"frontier_{profile}.txt")
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        c, ms, w, mst, wt, s = line.split("\t")
        out.append((float(c), float(ms), float(w), float(mst), float(wt), s))
    return out


def entries(profile="dev-at"):
    e = [(n, layouts.to_mapping(n)) for n in layouts.ALL]
    for fname, label in ((f"result_final_{profile}.txt", "ZEHN"),
                         (f"result_sim_{profile}.txt", "MECH")):
        p = pathlib.Path(fname)
        if p.exists():
            s = p.read_text(encoding="utf-8").split()[0]
            e.append((label, layouts.to_mapping(label, s)))
    return e


# --------------------------------------------------------------------------------------
def fig_frontier(profile, sc_test, u_test):
    """Comfort-constrained frontier: what does sparing the weak fingers actually cost?"""
    from frontier import weak_share
    import layouts as L

    tsv = pathlib.Path(f"constrained_frontier_{profile}.tsv")
    if not tsv.exists():
        print("  (no constrained frontier, skipping fig 1)")
        return
    sim = simfast.SimScorer(gap=30.0)

    feas_x, feas_y, inf_x, inf_y = [], [], [], []
    for line in tsv.read_text(encoding="utf-8").splitlines()[1:]:
        cap, mst, wt, home, sc_, rd, ok, lay = line.split("	")
        perm = simfast.mapping_to_perm(L.to_mapping("c" + cap, lay))
        x = weak_share(perm, u_test)
        y = sim.ms_per_char(perm, sc_test)
        (feas_x if ok == "YES" else inf_x).append(x)
        (feas_y if ok == "YES" else inf_y).append(y)

    fig, ax = plt.subplots(figsize=(8.6, 5.6))

    allx = feas_x + inf_x
    ally = feas_y + inf_y
    o = np.argsort(allx)
    ax.plot(np.array(allx)[o], np.array(ally)[o], "-", color=S1, lw=2, alpha=0.45, zorder=2)
    ax.plot(inf_x, inf_y, "o", color=SURFACE, ms=8, mec=S1, mew=2, zorder=4,
            label="constrained search, comfort box broken")
    ax.plot(feas_x, feas_y, "o", color=S1, ms=8, mec=SURFACE, mew=2, zorder=5,
            label="constrained search, comfort box met")

    offsets = {"AdNW": (10, -4), "AdNWzjßf": (10, 4), "KOY": (4, -16), "KOU": (10, 4),
               "VOU": (-30, 4), "Bone": (10, 2), "Neo2": (10, 2), "QWERTZ": (10, 2)}
    for name, mapping in entries(profile):
        if name in ("ZEHN", "MECH"):
            continue
        perm = simfast.mapping_to_perm(mapping)
        x = weak_share(perm, u_test)
        y = sim.ms_per_char(perm, sc_test)
        col = S3 if name == "QWERTZ" else S2
        ax.plot([x], [y], "o", color=col, ms=8, mec=SURFACE, mew=2, zorder=6)
        ax.annotate(name, (x, y), textcoords="offset points",
                    xytext=offsets.get(name, (9, 3)), fontsize=9, color=INK2, zorder=7)

    avail = {n: m for n, m in entries(profile)}
    if "ZEHN" in avail:
        perm = simfast.mapping_to_perm(avail["ZEHN"])
        x = weak_share(perm, u_test)
        y = sim.ms_per_char(perm, sc_test)
        ax.plot([x], [y], "*", color=S1, ms=20, mec=SURFACE, mew=1.5, zorder=8)
        ax.annotate("ZEHN", (x, y), textcoords="offset points", xytext=(-4, 16),
                    fontsize=11, color=S1, weight="bold", zorder=9, ha="center")
        ax.annotate("", xy=(x, y), xytext=(41.3, y),
                    arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.2, ls=(0, (4, 3))))
        label = "6.7 points of load off the weak" + chr(10) + "fingers, same speed and comfort"
        ax.text(34.5, 33.75, label, ha="left", va="top", fontsize=9, color=INK2)

    ax.plot([], [], "o", color=S2, ms=8, label="published German layouts")
    ax.plot([], [], "o", color=S3, ms=8, label="QWERTZ (baseline)")
    ax.set_xlabel("keystrokes on the weak fingers  —  pinkies + ring fingers, % of total")
    ax.set_ylabel("simulated typing time  (ms per character, lower is faster)")
    ax.set_title("AdNW and KOY are fast because they overwork the weak fingers",
                 fontsize=13, color=INK, pad=14, loc="left")
    ax.legend(frameon=False, loc="upper right", fontsize=9)
    fig.text(0.125, 0.005,
             "Every point on the curve also matches AdNW on home-row share, scissors and "
             "redirects. Hollow points break that box.",
             fontsize=8.5, color=MUTED)
    _clean(ax)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(FIG / "fig1_frontier.png", dpi=170)
    plt.close(fig)
    print("  fig1_frontier.png")


def fig_travel(profile, test, hover_text):
    names, hov, ret = [], [], []
    for name, mapping in entries(profile):
        names.append(name)
        hov.append(travel_hover(mapping, hover_text))
        ret.append(travel_return(mapping, test))
    order = np.argsort(hov)
    names = [names[i] for i in order]
    hov = np.array(hov)[order]
    ret = np.array(ret)[order]

    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    y = np.arange(len(names))
    h = 0.38
    ax.barh(y + h / 2 + 0.02, hov, height=h, color=S1, label="fingers hover (skilled)")
    ax.barh(y - h / 2 - 0.02, ret, height=h, color=S2, label="fingers return home (textbook)")
    for i, (a, b) in enumerate(zip(hov, ret)):
        ax.text(a + 0.25, i + h / 2 + 0.02, f"{a:.1f}", va="center", fontsize=8.5, color=INK2)
        ax.text(b + 0.25, i - h / 2 - 0.02, f"{b:.1f}", va="center", fontsize=8.5, color=INK2)
    ax.set_yticks(y, names)
    ax.set_xlabel("millimetres of finger travel per character typed")
    ax.set_title("How far your fingers actually move  —  no tunable parameters",
                 fontsize=13, color=INK, pad=14, loc="left")
    ax.legend(frameon=False, loc="lower right", fontsize=9)
    ax.grid(axis="y", visible=False)
    _clean(ax)
    fig.tight_layout()
    fig.savefig(FIG / "fig2_travel.png", dpi=170)
    plt.close(fig)
    print("  fig2_travel.png")


def fig_sfb(profile, test):
    names, sfb, forced = [], [], []
    for name, mapping in entries(profile):
        s, f = collisions(mapping, test)
        names.append(name)
        sfb.append(s)
        forced.append(f)
    order = np.argsort(sfb)
    names = [names[i] for i in order]
    sfb = np.array(sfb)[order]

    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    cols = [{"QWERTZ": S3, "ZEHN": S1, "MECH": S4}.get(n, S2) for n in names]
    bars = ax.bar(names, sfb, color=cols, width=0.62)
    for b, v in zip(bars, sfb):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.12, f"{v:.2f}%",
                ha="center", fontsize=8.5, color=INK2)
    ax.set_ylabel("same-finger bigrams, % of all bigrams")
    ax.set_title("One finger asked to do two jobs in a row",
                 fontsize=13, color=INK, pad=14, loc="left")
    ax.grid(axis="x", visible=False)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    _clean(ax)
    fig.tight_layout()
    fig.savefig(FIG / "fig3_samefinger.png", dpi=170)
    plt.close(fig)
    print("  fig3_samefinger.png")


def fig_sweep(profile, sc_test):
    gaps = np.arange(24, 92, 4.0)
    picks = ["QWERTZ", "Neo2", "AdNW"]
    p = pathlib.Path(f"result_sim_{profile}.txt")
    extra = []
    if p.exists():
        extra.append(("MECH", layouts.to_mapping("MECH", p.read_text(encoding="utf-8").split()[0])))
    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    series = [(n, layouts.to_mapping(n)) for n in picks] + extra
    colors = [S3, S2, S2, S1]
    styles = ["-", "--", "-", "-"]
    for (name, mapping), col, st in zip(series, colors, styles):
        perm = simfast.mapping_to_perm(mapping)
        ys = []
        for g in gaps:
            ys.append(simfast.SimScorer(gap=float(g)).ms_per_char(perm, sc_test) - g)
        ax.plot(gaps, ys, st, color=col, lw=2, label=name)
        ax.annotate(name, (gaps[0], ys[0]), textcoords="offset points",
                    xytext=(-6, 0), ha="right", fontsize=9, color=INK2)
    ax.set_xlabel("motor sequencing interval (ms)  —  left = a faster typist")
    ax.set_ylabel("time lost to fingers not being ready (ms/char)")
    ax.set_title("A layout is worth more the faster you already type",
                 fontsize=13, color=INK, pad=14, loc="left")
    ax.legend(frameon=False, fontsize=9)
    fig.text(0.125, 0.005,
             "Only the layout-attributable part is plotted: total time minus the "
             "sequencing floor everyone pays.", fontsize=8.5, color=MUTED)
    _clean(ax)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(FIG / "fig4_speed_dependence.png", dpi=170)
    plt.close(fig)
    print("  fig4_speed_dependence.png")


def fig_fingerload(profile, test):
    from keyboard import FINGER_NAMES
    picks = ["QWERTZ", "AdNW", "ZEHN", "MECH"]
    avail = {n: m for n, m in entries(profile)}
    picks = [p for p in picks if p in avail]
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    width = 0.8 / len(picks)
    x = np.arange(8)
    weakset = (0, 1, 6, 7)
    palette = {"QWERTZ": S3, "AdNW": S2, "ZEHN": S1, "MECH": S4}
    for i, name in enumerate(picks):
        load = np.zeros(8)
        for c, n in test.unigrams.items():
            f = KEYS[avail[name][c]].finger
            if f != TH:
                load[f] += n
        share = 100 * load / load.sum()
        ax.bar(x + i * width - 0.4 + width / 2, share, width * 0.86,
               color=palette.get(name, S1), label=name)
    ax.axhspan(-0.5, 0, color=SURFACE)
    for f in weakset:
        ax.axvspan(f - 0.5, f + 0.5, color="#f2f1ec", zorder=0)
    ax.set_xticks(x, [FINGER_NAMES[f].replace("-", "\n") for f in range(8)], fontsize=8.5)
    ax.set_ylabel("share of keystrokes (%)")
    ax.set_title("Where the work lands  —  shaded columns are the weak fingers",
                 fontsize=13, color=INK, pad=34, loc="left")
    ax.legend(frameon=False, fontsize=9.5, ncol=4, loc="lower right",
              bbox_to_anchor=(1.0, 1.005))
    ax.set_ylim(0, 24)
    ax.grid(axis="x", visible=False)
    _clean(ax)
    fig.tight_layout()
    fig.savefig(FIG / "fig5_fingerload.png", dpi=170)
    plt.close(fig)
    print("  fig5_fingerload.png")


def _draw_board(ax, mapping, freq, title):
    """One keyboard, keys shaded by how often they are struck."""
    inv = {slot: ch for ch, slot in mapping.items()}
    vmax = max(freq.values()) if freq else 1.0
    for slot in SLOTS_32:
        k = KEYS[slot]
        ch = inv.get(slot, "")
        f = freq.get(ch, 0.0) / vmax if ch else 0.0
        # sequential single hue, light -> dark
        col = (1 - 0.72 * f, 1 - 0.55 * f, 1 - 0.20 * f)
        x = k.x / 19.05 - 0.46
        y = -(k.y / 19.05) - 0.46
        ax.add_patch(FancyBboxPatch((x, y), 0.92, 0.92,
                                    boxstyle="round,pad=0,rounding_size=0.12",
                                    linewidth=1.0, edgecolor="#d8d7d2", facecolor=col))
        glyph = "ß" if ch == "ß" else ch.upper()
        ax.text(x + 0.46, y + 0.46, glyph, ha="center", va="center",
                fontsize=11, color="#ffffff" if f > 0.55 else INK)
    ax.set_xlim(1.0, 13.2)
    ax.set_ylim(-4.2, -0.7)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=11.5, color=INK, loc="left", pad=6)


def fig_boards(profile, test):
    avail = {n: m for n, m in entries(profile)}
    picks = [p for p in ("QWERTZ", "AdNW", "ZEHN", "MECH") if p in avail]
    freq = {c: n / test.total for c, n in test.unigrams.items()}
    fig, axes = plt.subplots(len(picks), 1, figsize=(7.6, 2.05 * len(picks)))
    if len(picks) == 1:
        axes = [axes]
    for ax, name in zip(axes, picks):
        _draw_board(ax, avail[name], freq, name)
    fig.suptitle("Key usage on the held-out corpus  —  darker is more frequent",
                 fontsize=13, color=INK, x=0.02, ha="left", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.975))
    fig.savefig(FIG / "fig6_keyboards.png", dpi=170)
    plt.close(fig)
    print("  fig6_keyboards.png")


def main():
    profile = sys.argv[1] if len(sys.argv) > 1 else "dev-at"
    base = data.base_corpora()
    _, test = data.mixes(base, profile)
    sc_test = simfast.SimCorpus(test)
    u_test = np.zeros(32)
    for c, n in test.unigrams.items():
        u_test[simfast.CIDX[c]] = n
    hover_text = sample_text("corpus/de_test", 300_000)

    print("writing figures/")
    fig_frontier(profile, sc_test, u_test)
    fig_travel(profile, test, hover_text)
    fig_sfb(profile, test)
    fig_sweep(profile, sc_test)
    fig_fingerload(profile, test)
    fig_boards(profile, test)


if __name__ == "__main__":
    main()
