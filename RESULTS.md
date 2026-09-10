# Results — finger assignment on German/Austrian QWERTZ

Every table is on **held-out text** (1.11M chars German, 1.90M English, 3.42M Python) that
the search never saw. Raw run logs are in [`results/`](results/).

The letters never move. The variable throughout is which finger presses which key.

---

## 1. The standard German ten-finger discipline

| finger | rests | keys |
|---|---|---|
| left pinky | `A` | `^` `1` `Q` `A` `<` `Y` |
| left ring | `S` | `2` `W` `S` `X` |
| left middle | `D` | `3` `E` `D` `C` |
| left index | `F` | `4` `5` `R` `T` `F` `G` `V` `B` |
| right index | `J` | `6` `7` `Z` `U` `H` `J` `N` `M` |
| right middle | `K` | `8` `I` `K` `,` |
| right ring | `L` | `9` `O` `L` `.` |
| right pinky | `Ö` | `0` `ß` `´` `P` `Ü` `+` `Ö` `Ä` `#` `-` |

Measured on held-out text:

| | value |
|---|---|
| simulated time | 48.594 ms/char |
| finger travel | 31.29 mm/char |
| weak-finger load (both pinkies + both rings) | 28.9% |

Load per finger:

| LP | LR | LM | LI | RI | RM | RR | RP |
|---|---|---|---|---|---|---|---|
| 7.8% | 8.2% | **20.8%** | **21.3%** | 18.9% | 10.2% | 10.4% | **2.5%** |

An even split would be 12.5% each. The left index does **8.5×** the work of the right pinky.

## 2. Searching the assignment space

An assignment is 7 finger boundaries per row across 3 letter rows — 21 integers, with
fingers ordered left to right and hands not crossing. The number row follows the top row
(shifted one column, since it is staggered 1.5u left). Resting keys follow the assignment:
each finger rests on the home-row key it owns nearest its anatomical column.

Simulated annealing, 6–8 restarts, 120k–140k iterations each.

| objective | time | travel | weak load | verdict |
|---|---|---|---|---|
| **standard discipline** | 48.594 | **31.29** | **28.9%** | the baseline |
| minimise time only | **47.026** (−3.2%) | 43.12 (+37.8%) | 53.6% | buys time with travel |
| minimise time, weak load ≤ 28.9% | 47.456 (−2.3%) | 41.32 (+32.1%) | 27.9% | same trade |
| minimise time, travel ≤ 31.29 **and** load ≤ 28.9% | 47.925 (−1.4%) | 31.64 (**+1.1%, over cap**) | 28.9% | **fails the box** |

The time-only optimum reassigns fingers so that long reaches happen while that finger is
idle. The simulated clock improves because the movement hides behind the other hand; the
hand still has to make the movement. Travel is the parameter-free check that catches this,
which is why it is in the box.

**Conclusion: no assignment beats the standard on time without spending more travel.** The
margin is not large — the best boxed candidate misses by 1.1% of travel — so the honest
statement is that the standard assignment sits on the frontier, not that it is uniquely
optimal.

For reference, the boxed candidate's assignment differed from standard in four places:
`<`→left ring, `B`→right index, `J`→right middle, `O`→right pinky. Each of those was then
tested in isolation (§3) and none survives alone.

## 3. Single-key reassignments

Each candidate moves exactly one key to an adjacent finger, everything else held fixed.
A change is worth making only if it improves simulated time **and** does not increase
travel.

| key | from | to | reach now | reach after | Δ ms/char | Δ travel | verdict |
|---|---|---|---|---|---|---|---|
| `Z` | RI | LI | 30.5 mm | 38.4 mm | −0.034 | +0.09 | no — costs travel |
| `Y` | LP | LR | 21.3 mm | 21.3 mm | −0.006 | ±0.00 | **KEEP** |
| `-` | RP | RR | 21.3 mm | 34.3 mm | ±0.000 | ±0.00 | no effect |
| `6` | RI | LI | 50.6 mm | 44.9 mm | ±0.000 | ±0.00 | geometry only |
| `<` | LP | LR | 21.3 mm | 34.3 mm | ±0.000 | ±0.00 | no effect |
| `Ü` | RP | RR | 23.8 mm | 38.4 mm | +0.007 | +0.08 | no |
| `B` | LI | RI | 34.3 mm | 34.3 mm | +0.045 | ±0.00 | no |
| `M` | RI | RM | 21.3 mm | 21.3 mm | +0.107 | ±0.00 | no |
| `H` | RI | RM | 19.0 mm | 38.1 mm | +0.139 | +1.66 | no |
| `G` | LI | LM | 19.0 mm | 38.1 mm | +0.262 | +0.89 | no |
| `T` | LI | LM | 23.8 mm | 38.4 mm | +0.475 | +2.13 | no |

**1 of 11 helps, and barely.** `Y` moving from the left pinky to the left ring is worth
−0.006 ms/char, which is the core of the angle mod (§6).

`B` is the interesting null: it is *exactly* equidistant from `F` and `J` (34.3 mm each), so
the choice looks arbitrary. It is not — giving it to the right index costs +0.045 ms/char,
because `B` follows and precedes left-hand letters far more often than right-hand ones in
German, and the right index is already busy with `H U N M Z`.

## 4. The symbol layer

Where the standard discipline genuinely does badly, and it is not the letters. Measured
over **1,526,672** symbol and punctuation keystrokes from the Python standard library.

AltGr is a **right-thumb** key. Cost model: base key cost, plus the modifier's own cost,
plus a penalty when modifier and key fall on the same hand (the hand is committed while it
reaches), plus a large penalty when they fall on the same finger.

| char | count | share | QWERTZ | cost | Neo layer 3 | cost | Δ |
|---|---|---|---|---|---|---|---|
| `_` | 178,849 | 11.7% | Shift `-` | 4.63 | Mod3 `w` | 3.27 | −1.36 |
| `'` | 151,672 | 9.9% | Shift `#` | 5.03 | Mod3 `.` | 3.53 | −1.49 |
| `"` | 139,215 | 9.1% | Shift `2` | 5.04 | Mod3 `,` | 3.05 | −1.99 |
| `)` | 123,933 | 8.1% | Shift `9` | 5.04 | Mod3 `k` | 1.95 | −3.09 |
| `(` | 123,906 | 8.1% | Shift `8` | 4.38 | Mod3 `j` | 1.90 | −2.48 |
| `:` | 97,117 | 6.4% | Shift `.` | 3.53 | Mod3 `ö` | 2.65 | −0.88 |
| `=` | 79,603 | 5.2% | Shift `0` | 5.91 | Mod3 `o` | 3.27 | −2.64 |
| `-` | 74,250 | 4.9% | `-` | 3.73 | Mod3 `l` | 2.25 | −1.48 |
| `#` | 61,338 | 4.0% | `#` | 4.13 | Mod3 `y` | 4.18 | **+0.05** |
| `>` | 32,491 | 2.1% | Shift `<` | 4.18 | Mod3 `i` | 2.80 | −1.38 |
| `\` | 31,789 | 2.1% | **AltGr `ß`** | 6.59 | Mod3 `a` | 2.65 | −3.94 |
| `[` | 20,095 | 1.3% | **AltGr `8`** | 4.73 | Mod3 `e` | 2.80 | −1.94 |
| `]` | 20,084 | 1.3% | **AltGr `9`** | 5.39 | Mod3 `r` | 2.72 | −2.67 |
| `{` | 6,265 | 0.4% | **AltGr `7`** | 4.62 | Mod3 `d` | 1.95 | −2.67 |
| `}` | 6,259 | 0.4% | **AltGr `0`** | 6.26 | Mod3 `f` | 1.90 | −4.36 |
| `;` | 4,031 | 0.3% | Shift `,` | 3.05 | Mod3 `-` | 4.63 | **+1.58** |
| | **all** | | | **3.77** | | **2.29** | **−39.2%** |

Two characters get worse — `#` and `;` — and are shown rather than dropped.

An earlier version of this model treated AltGr as a right-*pinky* key and produced costs
around 13 units for `\` and `}`. That was wrong; the corrected thumb model is what is
tabulated.

## 5. Shift discipline

German capitalises every noun, so a German typist shifts far more often than an English one.

| corpus | capitals as % of letters |
|---|---|
| German, modern (Wikipedia) | **8.32%** |
| German, 19th century (Gutenberg) | 5.18% |
| English | 2.59% |

Cost per capital, opposite-hand Shift versus same-hand:

| layout | German opp | German same | penalty | English opp | English same | penalty |
|---|---|---|---|---|---|---|
| QWERTZ | 2.76 | 4.95 | **+79%** | 2.97 | 5.60 | +89% |
| Neo2 | 2.81 | 5.08 | +81% | 2.64 | 4.65 | +76% |
| AdNW | 2.92 | 6.41 | +120% | 2.66 | 5.27 | +98% |
| KOY | 2.91 | 6.40 | +120% | 2.62 | 5.23 | +100% |

At modern German capitalisation rates, using the wrong Shift costs about **4.2% of total
typing effort**. It is the largest habit-level saving available on the letters.

## 6. The ISO angle mod

The left bottom row shifts one key left onto `<`: pinky takes `<`, ring `Y`, middle `X`,
index `C` and `V`. The letter-to-finger *ordering* is unchanged, so only geometry improves.

| layout | effort standard | angle | change | travel standard | angle |
|---|---|---|---|---|---|
| QWERTZ | 2707.7 | 2691.8 | **−0.6%** | 31292 | 30842 |
| Neo2 | 2145.9 | 2142.3 | −0.2% | 17623 | 17475 |
| AdNW | 1751.3 | 1750.5 | −0.0% | 16385 | 16356 |
| KOY | 1763.2 | 1762.1 | −0.1% | 16223 | 16189 |

Free, and small. QWERTZ benefits most because the mod mainly rescues `B` at 34.3 mm, and an
optimised layout would not have put a common letter there.

## 7. Backspace

Backspace sits 57 mm from the right pinky's resting key — the longest reach on the board.
Modelled cost 6.30 effort units against roughly 0.35 for a thumb key.

| Backspace as % of keystrokes | effort saved |
|---|---|
| 2.0% | 4.4% |
| 4.0% | 8.8% |
| 5.9% | 13.0% |
| 6.5% | 14.3% |
| 8.0% | 17.6% |

Rates from Dhakal et al., CHI 2018 (136M keystrokes): 5.9% for trained typists, 6.5% for
untrained, KSPC 1.173, Backspace among the three most-pressed keys.

## 8. Reach from each finger's resting key

| finger | keys, mm |
|---|---|
| left pinky (`A`) | q 20 · a 0 · < 21 · y 21 · 1 41 · ^ **51** |
| left ring (`S`) | w 20 · s 0 · x 21 · 2 41 |
| left middle (`D`) | e 20 · d 0 · c 21 · 3 41 |
| left index (`F`) | r 20 · t 24 · f 0 · g 19 · v 21 · b **34** · 4 41 · 5 38 |
| right index (`J`) | z **31** · u 20 · h 19 · j 0 · n 21 · m 21 · 6 **51** · 7 41 |
| right middle (`K`) | i 20 · k 0 · , 21 · 8 41 |
| right ring (`L`) | o 20 · l 0 · . 21 · 9 41 |
| right pinky (`Ö`) | p 20 · ü 24 · + 38 · ö 0 · ä 19 · # 38 · - 21 · 0 41 · ß 38 · ´ **45** |

Longest reaches: `^` 50.6 · `6` 50.6 · `´` 44.9 · `9`/`3`/`2`/`1`/`8`/`7`/`4`/`0` 40.7 ·
`ß`/`5`/`+` 38.4 · `#` 38.1 · `b` 34.3 · `z` 30.5.

## 9. The simulator, and why it can be trusted

The closed-form stall model used inside the searches is validated against the sequential
simulator on 300k characters of held-out German:

```
layout         simulator   closed form     diff
QWERTZ            48.513        48.996    0.483
Neo2              47.662        47.982    0.319
Bone              46.455        46.543    0.088
AdNW              46.241        46.287    0.046
AdNWzjßf          46.240        46.286    0.046
KOY               46.244        46.291    0.047
KOU               46.328        46.391    0.063
VOU               46.449        46.536    0.086

correlation 1.0000   ranking identical: True   MAE 0.147 ms/char
```

The closed form slightly overestimates because it ignores that a stall pushes later
keystrokes back, giving fingers extra time — a second-order effect, largest for the worst
layout, so conservative in the direction that matters.

## Files

| | |
|---|---|
| [`results/fingersearch_log.txt`](results/fingersearch_log.txt) | the assignment search and decisive test |
| [`results/keytweaks_log.txt`](results/keytweaks_log.txt) | single-key reassignments |
| [`results/fingermap_dev-at.txt`](results/fingermap_dev-at.txt) | the assignments found, machine-readable |
| [`results/shift_log.txt`](results/shift_log.txt) | Shift discipline and Backspace |
| [`results/anglemod_log.txt`](results/anglemod_log.txt) | ISO angle mod |
| [`results/efficiency_log.txt`](results/efficiency_log.txt) | parameter-free measures and the 36-point sweep |
