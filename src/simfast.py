"""The simulator's mechanics, solved analytically so they can be optimised against.

Running the full sequential simulator inside an annealer is far too slow, but its
behaviour can be derived in closed form.

In the simulator a keystroke is delayed only when the finger it needs is still busy or
still travelling. If a finger pressed a key L keystrokes ago, it has had L sequencing
intervals to get where it is going, so the delay it causes is

    stall(a, b, L) = max(0, DWELL + travel_time(distance(a, b)) - L * GAP)

and this is non-zero only when a and b are on the same finger. Total time per character
is therefore

    ms_per_char  =  GAP  +  sum over L, over same-finger pairs at lag L,
                            of P(pair) * stall(pair, L)

There are no free parameters beyond the three physical ones. Nothing here encodes an
opinion about whether pinkies are worth 1.75 of an index finger.

verify_against_simulator() checks this closed form against the sequential simulator on
real text.
"""

from __future__ import annotations

import sys

import numpy as np

from keyboard import KEYS, SLOTS_32, dist
from simulate import DWELL, GAP, SPEED, T_MOVE, travel_time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CHARS = "abcdefghijklmnopqrstuvwxyzäöüß,."
CIDX = {c: i for i, c in enumerate(CHARS)}
NS = len(SLOTS_32)
MAX_LAG = 4


def stall_tables(dwell: float = DWELL, gap: float = GAP,
                 t_move: float = T_MOVE, speed: float = SPEED) -> list[np.ndarray]:
    """S[L][i, j] = milliseconds lost when slot j follows slot i, L keystrokes later."""
    out = []
    for L in range(1, MAX_LAG + 1):
        S = np.zeros((NS, NS))
        for i, si in enumerate(SLOTS_32):
            ki = KEYS[si]
            for j, sj in enumerate(SLOTS_32):
                kj = KEYS[sj]
                if ki.finger != kj.finger:
                    continue          # different actuators never block each other
                d = dist(ki, kj)
                S[i, j] = max(0.0, dwell + travel_time(d, t_move, speed) - L * gap)
        out.append(S)
    return out


def travel_table() -> np.ndarray:
    """D[i, j] = mm the finger moves when slot j follows slot i on the same finger."""
    D = np.zeros((NS, NS))
    for i, si in enumerate(SLOTS_32):
        for j, sj in enumerate(SLOTS_32):
            if KEYS[si].finger == KEYS[sj].finger:
                D[i, j] = dist(KEYS[si], KEYS[sj])
    return D


class SimCorpus:
    """Lag tables packed as dense character matrices, normalised to per-keystroke rates."""

    def __init__(self, ng):
        self.name = ng.name
        self.total = float(ng.total)
        self.L = []
        for lag in range(1, MAX_LAG + 1):
            M = np.zeros((32, 32))
            for (a, b), n in ng.lags[lag].items():
                M[CIDX[a], CIDX[b]] = n
            self.L.append(M / self.total)
        # for the travel metric: where does a finger go next, at any lag, first hit only
        self.first = self.L[0]


class SimScorer:
    def __init__(self, dwell: float = DWELL, gap: float = GAP,
                 t_move: float = T_MOVE, speed: float = SPEED):
        self.S = stall_tables(dwell, gap, t_move, speed)
        self.D = travel_table()
        self.gap = gap

    def ms_per_char(self, perm: np.ndarray, sc: SimCorpus) -> float:
        total = self.gap
        for lag in range(MAX_LAG):
            sub = self.S[lag][np.ix_(perm, perm)]
            total += float((sc.L[lag] * sub).sum())
        return total

    def stall_only(self, perm: np.ndarray, sc: SimCorpus) -> float:
        return self.ms_per_char(perm, sc) - self.gap


def mapping_to_perm(mapping: dict[str, str]) -> np.ndarray:
    """char -> slot index, as a strict permutation of the 32 slots.

    QWERTZ is the awkward case: its 'ß' lives on the number row, which is outside the
    32-slot space, and it spends a main-block slot on '-', which is outside the scored
    alphabet. Any character that cannot be placed is therefore assigned to whichever
    slot is left over -- for QWERTZ that puts 'ß' on the '-' key (bottom right, right
    pinky) instead of the number row.

    That is *charitable to QWERTZ*: the real key is further away than the substitute, so
    QWERTZ's disadvantage is understated rather than exaggerated.

    An earlier version silently left unplaced characters at slot 0, which put 'ß' on top
    of 'q' and made every permutation-based QWERTZ figure wrong. The assertion below
    exists so that can never happen again.
    """
    slot_idx = {s: i for i, s in enumerate(SLOTS_32)}
    perm = np.full(32, -1, dtype=np.int64)
    used = set()
    for c, s in mapping.items():
        if c in CIDX and s in slot_idx:
            perm[CIDX[c]] = slot_idx[s]
            used.add(slot_idx[s])
    spare = [i for i in range(NS) if i not in used]
    for ci in range(32):
        if perm[ci] < 0:
            perm[ci] = spare.pop(0)
    assert sorted(perm.tolist()) == list(range(32)), "mapping_to_perm produced a collision"
    return perm


def perm_to_string(perm: np.ndarray) -> str:
    out = [""] * 32
    for ci, si in enumerate(perm):
        out[si] = CHARS[ci]
    return "".join(out)


def verify_against_simulator(text: str, names) -> None:
    """The closed form must track the sequential simulator, layout by layout."""
    import corpora
    import layouts
    from simulate import Simulator

    ng = corpora.Ngrams("verify", text)
    sc = SimCorpus(ng)
    sim = SimScorer()

    print(f"{'layout':<12}{'simulator':>12}{'closed form':>14}{'diff':>9}")
    print("-" * 47)
    exact, approx = [], []
    for n in names:
        # Compare like with like: both sides see the layout as the 32-slot permutation
        # sees it, so QWERTZ's number-row 'ß' substitution is applied to both.
        perm = mapping_to_perm(layouts.to_mapping(n))
        m = layouts.to_mapping(n + "_perm", perm_to_string(perm))
        a = Simulator(m).run(text).ms_per_char
        b = sim.ms_per_char(perm, sc)
        exact.append(a)
        approx.append(b)
        print(f"{n:<12}{a:>12.3f}{b:>14.3f}{b - a:>9.3f}")
    r = np.corrcoef(exact, approx)[0, 1]
    order_ok = [n for _, n in sorted(zip(exact, names))] == [n for _, n in sorted(zip(approx, names))]
    print(f"\ncorrelation {r:.4f}   ranking identical: {order_ok}")
    print(f"mean absolute error {np.mean(np.abs(np.array(exact) - np.array(approx))):.3f} ms/char")


if __name__ == "__main__":
    import layouts
    from simulate import sample_text

    text = sample_text("corpus/de_test", 300_000)
    print(f"validating the closed form on {len(text):,} characters of held-out German\n")
    verify_against_simulator(text, layouts.ALL)
