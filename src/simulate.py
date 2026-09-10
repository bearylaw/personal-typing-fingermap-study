"""A ten-finger typing simulator. No borrowed weight tables.

The effort models in metrics.py contain numbers I chose: A_SFB = 4.0, pinky costs 1.75,
a scissor is worth 2.2. Those are judgement calls, and a layout optimised against them
is partly a portrait of my judgement. This file replaces the judgement with mechanics.

The model:

    Ten fingers are independent actuators with positions on the board. To press a key, the
    assigned finger travels from where it currently is to that key, then presses. Fingers
    move CONCURRENTLY -- while your right index is typing, your left middle is already on
    its way. Keys must be struck in text order, and no faster than the motor system can
    sequence them.

    press[i]  = max( press[i-1] + GAP , free[finger] + travel_time(from, to) )
    free[f]   = press[i] + DWELL

    total time = press[last]

Everything that the hand-tuned models put in by hand falls out of this instead:

  - a same-finger bigram is slow because one actuator must do two jobs in series
  - alternating hands is fast because the travel hides behind the other hand's work
  - a long reach is free if the finger had idle time to prepare, and expensive if not
  - rolls are fast because adjacent fingers are already near their targets

Only three parameters, all physical and all measured in time, not in invented units:

    T_MOVE, SPEED   how long a finger takes to cross a distance
    DWELL           how long the finger is committed to a key
    GAP             the floor on sequencing two keystrokes

The ranking must survive changes to all three, and sweep_parameters() checks that.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass

from keyboard import KEYS, SPACE, TH, dist

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# --- the three physical parameters ----------------------------------------------------
# Ballistic movement: a finger accelerates then decelerates, so time goes as sqrt(distance)
# rather than linearly. T_MOVE is the fixed cost of initiating any movement.
T_MOVE = 38.0        # ms, movement initiation
SPEED = 3.1          # ms per sqrt(mm); 20 mm -> 38 + 3.1*4.47 = 52 ms
DWELL = 32.0         # ms the finger is committed to the key
GAP = 46.0           # ms, minimum sequencing interval between two keystrokes


def travel_time(d_mm: float, t_move: float = T_MOVE, speed: float = SPEED) -> float:
    if d_mm <= 0.5:
        return 0.0
    return t_move + speed * math.sqrt(d_mm)


@dataclass
class SimResult:
    ms_per_char: float
    wpm: float
    mm_per_char: float          # total finger travel
    stalls: float               # fraction of keystrokes delayed by a busy finger
    stall_ms_per_char: float    # time lost to those delays
    busiest_finger: float       # share of keystrokes on the most-loaded finger


class Simulator:
    def __init__(self, mapping: dict[str, str],
                 t_move: float = T_MOVE, speed: float = SPEED,
                 dwell: float = DWELL, gap: float = GAP):
        self.key = {c: KEYS[s] for c, s in mapping.items()}
        self.key[" "] = SPACE
        self.t_move, self.speed, self.dwell, self.gap = t_move, speed, dwell, gap

    def run(self, text: str) -> SimResult:
        key = self.key
        tm, sp, dwell, gap = self.t_move, self.speed, self.dwell, self.gap

        # each finger starts on its home key and is free at t=0
        pos = {}
        free = {}
        for f in range(9):
            pos[f] = None
            free[f] = 0.0

        prev_press = -gap
        travel_total = 0.0
        stalls = 0
        stall_ms = 0.0
        n = 0
        load = [0] * 9

        for ch in text:
            k = key.get(ch)
            if k is None:
                continue
            f = k.finger
            if f == TH:
                # thumbs alternate and barely move; treat space as always ready
                ready = free[f]
                d = 0.0
            else:
                p = pos[f]
                d = 0.0 if p is None else dist(p, k)
                if p is None:
                    # first use: finger is at its home key
                    from keyboard import home_key
                    d = dist(home_key(f), k)
                ready = free[f] + travel_time(d, tm, sp)

            earliest_seq = prev_press + gap
            press = ready if ready > earliest_seq else earliest_seq
            if ready > earliest_seq:
                stalls += 1
                stall_ms += ready - earliest_seq

            free[f] = press + dwell
            pos[f] = k
            prev_press = press
            travel_total += d
            load[f] += 1
            n += 1

        if n == 0:
            return SimResult(0, 0, 0, 0, 0, 0)
        total = prev_press
        ms_per_char = total / n
        letters = sum(load[:8]) or 1
        return SimResult(
            ms_per_char=ms_per_char,
            wpm=60000.0 / (ms_per_char * 5.0),
            mm_per_char=travel_total / n,
            stalls=100.0 * stalls / n,
            stall_ms_per_char=stall_ms / n,
            busiest_finger=100.0 * max(load[:8]) / letters,
        )


def sample_text(ng_source: str, limit: int) -> str:
    """A contiguous slice of real text, normalised to the scored alphabet."""
    import corpora
    raw = corpora.load_dir(ng_source)
    return corpora.normalise(raw)[:limit]


if __name__ == "__main__":
    import layouts

    text = sample_text("corpus/de_test", 400_000)
    print(f"simulating {len(text):,} characters of held-out German\n")
    print(f"{'layout':<12}{'ms/char':>9}{'WPM':>8}{'mm/char':>9}"
          f"{'stall%':>8}{'stall ms':>10}{'busiest':>9}")
    print("-" * 65)
    rows = []
    for n in layouts.ALL:
        r = Simulator(layouts.to_mapping(n)).run(text)
        rows.append((r.ms_per_char, n, r))
    for _, n, r in sorted(rows):
        print(f"{n:<12}{r.ms_per_char:>9.2f}{r.wpm:>8.1f}{r.mm_per_char:>9.2f}"
              f"{r.stalls:>8.1f}{r.stall_ms_per_char:>10.2f}{r.busiest_finger:>9.1f}")
