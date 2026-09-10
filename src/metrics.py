"""Scoring: model-free counters plus two deliberately independent effort models.

Why two models: the layout is optimised against Model A, so reporting that it wins on
Model A proves nothing. Model B is built on a different principle (movement *time* via
Fitts' law) with different parameters, and the model-free counters have no parameters at
all. Agreement across all three is the actual evidence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from keyboard import (
    FINGER_RANK,
    KEYS,
    LEFT,
    PITCH,
    RIGHT,
    SPACE,
    TH,
    dist,
    hand,
    is_stretch,
    travel_from_home,
)

# --------------------------------------------------------------------------------------
# Model A — biomechanical effort units
# --------------------------------------------------------------------------------------
A_FINGER_COST = {0: 1.75, 1: 1.35, 2: 1.05, 3: 1.00, 4: 1.00, 5: 1.05, 6: 1.35, 7: 1.75}
A_ROW_PEN = {1: 1.20, 2: 0.25, 3: 0.00, 4: 0.45}
A_TRAVEL = 0.55        # per key-pitch away from home
A_STRETCH = 0.45
A_SFB = 4.0            # same finger, different key
A_SFB_DIST = 1.0       # scaled by separation
A_SKIP = 0.9           # same finger with one key in between
A_ROWJUMP = 0.30
A_SCISSOR = 2.20
A_ROLL_IN = -0.35
A_ROLL_OUT = 0.25
A_ALTERNATE = -0.20
A_REDIRECT = 1.00
A_REDIRECT_NOIDX = 1.10   # additional, if no index finger rescues the direction change
A_BALANCE = 12.0          # weight on finger-load imbalance

# Target share of keystrokes per finger (index and middle carry more, pinkies less).
A_TARGET_LOAD = {0: 0.08, 1: 0.10, 2: 0.14, 3: 0.18, 4: 0.18, 5: 0.14, 6: 0.10, 7: 0.08}

# --------------------------------------------------------------------------------------
# Model B — movement time in milliseconds (Fitts' law), independent parameters
# --------------------------------------------------------------------------------------
B_TAP = 62.0           # ms floor for any keystroke
B_FITTS_A = 20.0
B_FITTS_B = 78.0       # ms per bit
B_WIDTH = 17.0         # effective target width, mm
B_ALT_BONUS = -14.0    # hands overlap in time
B_ROLL_IN_BONUS = -9.0
B_ROLL_OUT_PEN = 7.0
B_ROWCHANGE = 11.0
B_SCISSOR = 26.0
B_PINKY = {0: 16.0, 1: 8.0, 2: 2.0, 3: 0.0, 4: 0.0, 5: 2.0, 6: 8.0, 7: 16.0}


def _fitts(d_mm: float) -> float:
    return B_FITTS_A + B_FITTS_B * math.log2(d_mm / B_WIDTH + 1.0)


@dataclass
class Result:
    layout: str
    corpus: str
    effort_a: float = 0.0          # Model A units per 1000 chars
    time_b: float = 0.0            # Model B ms per char
    wpm_b: float = 0.0             # implied words per minute
    sfb: float = 0.0               # % of bigrams
    skipgram: float = 0.0
    same_hand: float = 0.0
    alternation: float = 0.0
    roll_in: float = 0.0
    roll_out: float = 0.0
    redirect: float = 0.0
    scissor: float = 0.0
    home_row: float = 0.0          # % of keystrokes
    travel_mm: float = 0.0         # mm per 1000 chars
    hand_balance: float = 0.0      # |left% - 50|
    finger_load: dict = field(default_factory=dict)
    max_finger: float = 0.0
    pinky_load: float = 0.0
    weak_load: float = 0.0         # pinkies + ring fingers, the ergonomically weak four

    def row(self) -> str:
        return (
            f"{self.layout:<12} {self.effort_a:8.1f} {self.wpm_b:7.1f} {self.sfb:6.2f} "
            f"{self.skipgram:6.2f} {self.home_row:6.1f} {self.travel_mm:8.0f} "
            f"{self.alternation:6.1f} {self.roll_in:6.1f} {self.redirect:6.2f} "
            f"{self.scissor:6.2f} {self.pinky_load:6.1f} {self.hand_balance:6.1f}"
        )


HEADER = (
    f"{'layout':<12} {'effortA':>8} {'wpm_B':>7} {'SFB%':>6} {'skip%':>6} {'home%':>6} "
    f"{'mm/1k':>8} {'alt%':>6} {'rollIn':>6} {'redir':>6} {'sciss':>6} {'pinky%':>6} {'imbal':>6}"
)


class Scorer:
    """Precomputes per-key and per-bigram tables for one layout, then folds a corpus."""

    def __init__(self, mapping: dict[str, str]):
        # mapping: character -> physical slot name
        self.mapping = mapping
        self.key = {c: KEYS[s] for c, s in mapping.items()}
        self.key[" "] = SPACE

        self._a_key: dict[str, float] = {}
        self._b_key: dict[str, float] = {}
        for c, k in self.key.items():
            if k.finger == TH:
                self._a_key[c] = 0.35
                self._b_key[c] = B_TAP
                continue
            travel = travel_from_home(k)
            a = A_FINGER_COST[k.finger] * (1.0 + A_TRAVEL * travel / PITCH)
            a += A_ROW_PEN[k.row]
            if is_stretch(k.slot):
                a += A_STRETCH
            self._a_key[c] = a
            self._b_key[c] = B_TAP + B_PINKY[k.finger] + 0.35 * _fitts(travel) if travel else B_TAP + B_PINKY[k.finger]

    # ---------------- bigram classification ----------------
    def classify(self, a: str, b: str):
        ka, kb = self.key[a], self.key[b]
        if ka.finger == TH or kb.finger == TH:
            return "space", ka, kb
        ha, hb = hand(ka.finger), hand(kb.finger)
        if ha != hb:
            return "alt", ka, kb
        if ka.finger == kb.finger:
            return "same" if a == b else "sfb", ka, kb
        ra, rb = FINGER_RANK[ka.finger], FINGER_RANK[kb.finger]
        rowdiff = abs(ka.row - kb.row)
        if abs(ra - rb) == 1 and rowdiff >= 2:
            return "scissor", ka, kb
        return ("roll_in" if rb < ra else "roll_out"), ka, kb

    def _a_bigram(self, a: str, b: str) -> float:
        kind, ka, kb = self.classify(a, b)
        if kind in ("space", "same"):
            return 0.0
        if kind == "alt":
            return A_ALTERNATE
        if kind == "sfb":
            return A_SFB + A_SFB_DIST * dist(ka, kb) / PITCH
        pen = A_ROWJUMP * abs(ka.row - kb.row)
        if kind == "scissor":
            return A_SCISSOR + pen
        return pen + (A_ROLL_IN if kind == "roll_in" else A_ROLL_OUT)

    def _b_bigram(self, a: str, b: str) -> float:
        kind, ka, kb = self.classify(a, b)
        if kind == "space":
            return 0.0
        if kind == "alt":
            return B_ALT_BONUS
        if kind == "same":
            return -12.0
        if kind == "sfb":
            return _fitts(dist(ka, kb)) + 34.0
        pen = B_ROWCHANGE * abs(ka.row - kb.row)
        if kind == "scissor":
            return B_SCISSOR + pen
        return pen + (B_ROLL_IN_BONUS if kind == "roll_in" else B_ROLL_OUT_PEN)

    # ---------------- corpus folding ----------------
    def score(self, ng, layout_name: str) -> Result:
        r = Result(layout=layout_name, corpus=ng.name)
        total = ng.total
        if total <= 0:
            return r

        # unigram-level
        load = {f: 0.0 for f in range(8)}
        travel = 0.0
        home = 0.0
        eff_a = 0.0
        time_b = 0.0
        left = 0.0
        for c, n in ng.unigrams.items():
            k = self.key[c]
            eff_a += self._a_key[c] * n
            time_b += self._b_key[c] * n
            if k.finger != TH:
                load[k.finger] += n
                travel += 2.0 * travel_from_home(k) * n   # out and back
                if travel_from_home(k) == 0.0:
                    home += n   # finger does not leave its resting key
                if k.finger in LEFT:
                    left += n

        # bigram-level
        bigrams_total = sum(ng.bigrams.values())
        counts = {k: 0.0 for k in ("alt", "sfb", "same", "roll_in", "roll_out", "scissor", "space")}
        for (a, b), n in ng.bigrams.items():
            eff_a += self._a_bigram(a, b) * n
            time_b += self._b_bigram(a, b) * n
            kind, _, _ = self.classify(a, b)
            counts[kind] += n

        # skipgrams (same finger with one key in between)
        skip_total = sum(ng.skipgrams.values())
        skip_bad = 0.0
        for (a, c), n in ng.skipgrams.items():
            ka, kc = self.key[a], self.key[c]
            if ka.finger != TH and ka.finger == kc.finger and a != c:
                skip_bad += n
                eff_a += A_SKIP * n

        # trigram redirects
        tri_total = sum(ng.trigrams.values())
        redirect = 0.0
        for (a, b, c), n in ng.trigrams.items():
            ka, kb, kc = self.key[a], self.key[b], self.key[c]
            if TH in (ka.finger, kb.finger, kc.finger):
                continue
            h = hand(ka.finger)
            if hand(kb.finger) != h or hand(kc.finger) != h:
                continue
            if ka.finger == kb.finger or kb.finger == kc.finger:
                continue
            d1 = FINGER_RANK[kb.finger] - FINGER_RANK[ka.finger]
            d2 = FINGER_RANK[kc.finger] - FINGER_RANK[kb.finger]
            if d1 * d2 < 0:
                redirect += n
                pen = A_REDIRECT
                if not any(FINGER_RANK[k.finger] == 1 for k in (ka, kb, kc)):
                    pen += A_REDIRECT_NOIDX
                eff_a += pen * n

        # finger-load imbalance (Model A only)
        keystrokes = sum(load.values()) or 1.0
        imbalance = 0.0
        for f in range(8):
            share = load[f] / keystrokes
            imbalance += (share - A_TARGET_LOAD[f]) ** 2
        eff_a += A_BALANCE * imbalance * total

        r.effort_a = 1000.0 * eff_a / total
        r.time_b = time_b / total
        r.wpm_b = 60000.0 / (r.time_b * 5.0) if r.time_b > 0 else 0.0
        r.sfb = 100.0 * counts["sfb"] / bigrams_total if bigrams_total else 0.0
        r.skipgram = 100.0 * skip_bad / skip_total if skip_total else 0.0
        r.same_hand = 100.0 * (counts["sfb"] + counts["same"] + counts["roll_in"]
                               + counts["roll_out"] + counts["scissor"]) / bigrams_total
        r.alternation = 100.0 * counts["alt"] / bigrams_total if bigrams_total else 0.0
        r.roll_in = 100.0 * counts["roll_in"] / bigrams_total if bigrams_total else 0.0
        r.roll_out = 100.0 * counts["roll_out"] / bigrams_total if bigrams_total else 0.0
        r.scissor = 100.0 * counts["scissor"] / bigrams_total if bigrams_total else 0.0
        r.redirect = 100.0 * redirect / tri_total if tri_total else 0.0
        r.home_row = 100.0 * home / keystrokes
        r.travel_mm = 1000.0 * travel / total
        r.hand_balance = abs(100.0 * left / keystrokes - 50.0)
        r.finger_load = {f: 100.0 * load[f] / keystrokes for f in range(8)}
        r.max_finger = max(r.finger_load.values())
        r.pinky_load = r.finger_load[0] + r.finger_load[7]
        r.weak_load = sum(r.finger_load[f] for f in (0, 1, 6, 7))
        return r


def effort_only(scorer: Scorer, ng) -> float:
    """Fast path used inside the optimiser: Model A total only."""
    return scorer.score(ng, "_").effort_a
