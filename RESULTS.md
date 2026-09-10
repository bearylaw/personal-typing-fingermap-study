# Results

Every table here is on **held-out text** unless marked otherwise. Raw run logs are in
[`results/`](results/). See [docs/METHOD.md](docs/METHOD.md) for what Level 0 / 1 / 2 mean;
the short version is that Level 0 has no tunable parameters, Level 1 has three physical
ones that are swept rather than chosen, and Level 2 is a weighted model that no conclusion
rests on.

Layouts under test: QWERTZ plus the seven published German-optimised layouts, taken
verbatim from the neo2-llkh driver source. `ZEHN` is this study's result. `MECH` is what
comes out of optimising the simulator alone with no comfort constraint — kept because its
failure mode is informative. `ZEHN-w` is the first attempt, optimised against the weighted
model — kept because it is the negative result the method exists to catch.

---

## 1. Level 0 — no tunable parameters

Geometry and corpus counts only.

| layout | travel HOVER<br>mm/char | travel RETURN<br>mm/char | same-finger<br>% of bigrams | forced serial<br>travel mm/char | busiest<br>finger % | weak-finger<br>load % | hand<br>imbalance |
|---|---|---|---|---|---|---|---|
| AdNWzjßf | **9.51** | 16.21 | 1.28 | 4.582 | 18.4 | 41.2 | 3.6 |
| AdNW | 9.60 | 16.38 | **1.28** | 4.626 | 18.4 | 41.2 | 3.6 |
| **ZEHN** | 9.63 | 16.68 | 1.39 | **4.485** | 18.7 | **34.8** | **1.0** |
| MECH | 9.64 | 20.89 | **1.19** | **3.628** | **14.7** | 47.3 | 3.1 |
| KOY | 9.73 | **16.22** | 1.31 | 4.709 | 18.7 | 38.0 | 3.6 |
| ZEHN-w | 9.73 | 16.43 | 1.31 | 4.624 | 19.5 | 37.1 | 1.4 |
| KOU | 10.25 | 16.22 | 1.60 | 4.959 | 20.4 | 38.8 | 3.1 |
| VOU | 10.68 | 16.80 | 1.73 | 5.151 | 20.4 | 37.6 | 4.8 |
| Bone | 10.70 | 18.67 | 2.38 | 5.635 | 25.9 | 33.4 | 4.5 |
| Neo2 | 11.16 | 17.62 | 7.56 | 7.815 | 25.3 | 28.7 | 1.7 |
| QWERTZ | 14.00 | 31.29 | 8.17 | 8.631 | 21.3 | **28.9** | 8.0 |

**HOVER** assumes a finger stays where it last pressed; **RETURN** assumes it goes home
after every press. The truth is between, so both are reported. QWERTZ is worst under both,
by a wide margin.

**Forced serial travel** is the movement a finger must make between two keystrokes close
enough in time (lags 1–4) that it cannot hide behind the other hand. ZEHN has the lowest of
any layout that respects the comfort constraints.

Note the last two columns together: QWERTZ has the *lowest* weak-finger load of any layout
here. It achieves that by hammering the index and middle fingers instead — and its hand
imbalance, 8.0, is by far the worst. Low weak-finger load is not on its own a virtue.

## 2. Level 1 — parallel-finger simulator, 36 parameter settings

Every combination of `GAP ∈ {30, 46, 62, 80} ms`, `DWELL ∈ {24, 32, 45} ms`, and three
movement-speed settings.

| layout | best ms/char | worst ms/char | mean rank | ranked 1st |
|---|---|---|---|---|
| MECH | 30.56 | 80.33 | 1.56 | 34/36 |
| AdNWzjßf | 30.71 | 80.35 | 2.92 | 0/36 |
| AdNW | 30.71 | 80.36 | 3.81 | 0/36 |
| ZEHN-w | 30.70 | 80.36 | 4.53 | 0/36 |
| KOY | 30.72 | 80.36 | 4.56 | 0/36 |
| ZEHN | 30.71 | 80.39 | 4.97 | 0/36 |
| KOU | 30.82 | 80.44 | 7.00 | 0/36 |
| VOU | 30.85 | 80.48 | 8.00 | 0/36 |
| Bone | 31.02 | 80.66 | 8.67 | 0/36 |
| Neo2 | 32.65 | 82.12 | 9.56 | 0/36 |
| QWERTZ | 32.97 | 82.37 | 10.44 | 2/36 |

QWERTZ ranks first in 2 of 36 — at the slowest sequencing settings, where every layout is
within a hair of every other and the ordering is effectively arbitrary. That is itself the
finding in §2 of the README: **at slow typing speeds the layout does not matter.**

| comparison | across the sweep |
|---|---|
| ZEHN vs QWERTZ | 0.0% to **16.9%** faster, mean 5.1% |
| AdNW vs QWERTZ | 0.0% to **16.4%** faster, mean 5.0% |

## 3. The decisive experiment — constrained search

Constraint box set to **AdNW's own** home-row share, scissor rate, redirect rate and
simulated time. Only the weak-finger cap is tightened. TRAIN figures; the search never saw
the test corpus.

| weak cap | ms/char | weak % | home-row % | scissors % | redirects % | inside the box | layout string |
|---|---|---|---|---|---|---|---|
| 41 | 31.772 | 40.8 | 60.7 | 0.08 | 3.44 | **YES** | `jßcwfü.öokzrntsmyieahglpdbvu,äqx` |
| 38 | 31.848 | 37.9 | 60.7 | 0.08 | 3.42 | **YES** | `jßcwfüöä.ykrntsmuieahglpdbv,xoqz` |
| **35** | **31.998** | **34.6** | **60.7** | **0.10** | **3.44** | **YES** | `lvdwfj,oqykrstncuieahgßzmbp.üöäx` |
| 32 | 32.159 | 31.9 | 60.7 | 0.08 | 3.35 | no | `pqo.yvwmxfzhaeiugtnrsbkäö,üdcljß` |
| 30 | 32.501 | 30.1 | 60.7 | 0.12 | 3.31 | no | `vßlgfü,zäjqsrntduieahpbxcmwy.oök` |
| 28 | 32.957 | 28.2 | 60.7 | 0.12 | 3.39 | no | `yöopbwmcqvxhaeiudtnrsküäz,.fgljß` |

Reference values for the box: AdNW = 32.064 ms/char, 41.7% weak, 60.7% home, 0.10%
scissors, 3.43% redirects.

The three infeasible rows fail on time only — they hold the comfort measures but cannot get
below AdNW's ms/char. **The frontier is real and it stops somewhere between 32% and 35%.**

### Held-out confirmation

| | ms/char | weak % | home-row % | scissors % | redirects % |
|---|---|---|---|---|---|
| **ZEHN** | **32.102** | **34.8** | 60.1 | 0.11 | 3.65 |
| AdNW | 32.198 | 41.2 | 60.1 | 0.11 | 3.71 |
| AdNWzjßf | 32.194 | 41.2 | 60.1 | 0.08 | 3.71 |
| KOY | 32.250 | 38.0 | 60.1 | 0.08 | 3.40 |
| QWERTZ | 36.179 | 28.9 | 25.0 | 5.64 | 12.62 |

## 4. Robustness across workloads

Held-out text, six different corpus mixes. The layout was searched on `dev-at` only.

| workload | layout | ms/char | weak % | home % | scissors % | redirects % |
|---|---|---|---|---|---|---|
| dev-at | **ZEHN** | 32.102 | **34.8** | 60.1 | 0.11 | 3.65 |
| | AdNW | 32.198 | 41.2 | 60.1 | 0.11 | 3.71 |
| pure German | **ZEHN** | 31.933 | **35.2** | 62.0 | 0.13 | 3.92 |
| | AdNW | 32.035 | 42.9 | 62.0 | 0.09 | 3.92 |
| pure English | **ZEHN** | 32.109 | **35.4** | 59.9 | 0.05 | 3.05 |
| | AdNW | 32.114 | 39.9 | 59.9 | 0.08 | 3.47 |
| pure code | **ZEHN** | 32.399 | **33.4** | 56.7 | 0.16 | 3.81 |
| | AdNW | 32.591 | 39.5 | 56.7 | 0.17 | 3.58 |
| 70% German | **ZEHN** | 32.015 | **35.1** | 61.1 | 0.11 | 3.75 |
| | AdNW | 32.107 | 42.0 | 61.1 | 0.10 | 3.81 |
| equal thirds | **ZEHN** | 32.145 | **34.7** | 59.6 | 0.11 | 3.62 |
| | AdNW | 32.245 | 40.8 | 59.6 | 0.11 | 3.67 |

The weak-finger gap ranges from −4.5 (English) to −7.7 (German) points and never reverses.

Over the 36-point physical sweep, **ZEHN minus AdNW ranges from −0.219 to +0.046 ms/char,
mean −0.018** — ZEHN is nominally faster in 14 of 36 settings and nominally slower in 22,
by amounts around 0.1%. **The correct summary is that the speed difference is a wash.**

## 5. The symbol layer

1,526,672 symbol and punctuation keystrokes from the Python standard library.

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

Two characters get worse — `#` and `;` — and they are shown rather than dropped.

AltGr is modelled as a **right-thumb** key. An earlier version modelled it as a right pinky
and produced costs around 13 units for `\` and `}`; that was wrong and the corrected model
is what is tabulated.

## 6. Shift and Backspace

| corpus | capitals as % of letters |
|---|---|
| German, modern (Wikipedia) | **8.82%** |
| German, 19th century (Gutenberg) | 5.18% |
| English | 2.59% |

Cost per capital, opposite-hand Shift versus same-hand:

| layout | German opp | German same | penalty | English opp | English same | penalty |
|---|---|---|---|---|---|---|
| QWERTZ | 2.76 | 4.95 | **+79%** | 2.97 | 5.60 | +89% |
| Neo2 | 2.81 | 5.08 | +81% | 2.64 | 4.65 | +76% |
| AdNW | 2.92 | 6.41 | **+120%** | 2.66 | 5.27 | +98% |
| KOY | 2.91 | 6.40 | +120% | 2.62 | 5.23 | +100% |

At German capitalisation rates, using the wrong Shift costs about **4.2% of total typing
effort**. The optimised layouts are *more* sensitive to this than QWERTZ, because they put
more frequent letters on the pinkies — the same fact as finding 3, showing up again.

Backspace sits 57 mm from the right pinky's home key; modelled cost 6.30 effort units
against roughly 0.35 for a thumb key.

| backspace as % of keystrokes | effort saved |
|---|---|
| 2.0% | 4.4% |
| 4.0% | 8.8% |
| 5.9% | 13.0% |
| 6.5% | 14.3% |
| 8.0% | 17.6% |

## 7. The ISO angle mod

Left bottom row shifted one key left onto the `<` key; fingers keep their columns, so the
letter-to-finger mapping is unchanged and only the geometry improves.

| layout | ms/char standard | angle | change | travel standard | angle |
|---|---|---|---|---|---|
| QWERTZ | 2704.5 | 2689.7 | **−0.5%** | 31554 | 31134 |
| ZEHN-w | 1672.0 | 1657.7 | −0.9% | 16552 | 16112 |
| Neo2 | 2148.1 | 2144.5 | −0.2% | 17714 | 17564 |
| AdNW | 1744.9 | 1744.2 | −0.0% | 16326 | 16299 |
| KOY | 1752.4 | 1751.2 | −0.1% | 16155 | 16117 |

*(Level 2 units — this comparison is about geometry, not about the absolute scale.)*

It helps every layout and it costs nothing, but it is small: it mainly rescues the `b` key
at 34.3 mm, and an optimised layout already avoids putting a frequent letter there.

## 8. The negative result, and why weight-perturbation does not rescue it

The first search optimised the Level-2 weighted model and produced `ZEHN-w`, scoring 4.7%
better than the best published layout **on that model**. On the untuned measures it was
*worse* than AdNW on same-finger bigrams (1.61 vs 1.17) and finger travel (+1.2%), and tied
on the independent Fitts-law model (+0.1%).

The instructive part is what happened next. Perturbing all 25 weights of the Level-2 model
by ±40%, 200 times, and re-ranking on held-out text:

| layout | wins % | top-2 % | mean rank | worst rank |
|---|---|---|---|---|
| ZEHN-w variants | 47–53 | 98–100 | 1.5 | 5 |
| AdNWzjßf | 0.0 | 1.5 | 3.20 | 4 |
| AdNW | 0.0 | 0.0 | 4.37 | 6 |
| KOY | 0.5 | 1.0 | 4.41 | 5 |
| QWERTZ | 0.0 | 0.0 | 10.00 | 10 |

A layout optimised against a model family still wins **99.5%** of randomly perturbed
weightings *within that family*. Sensitivity analysis over your own parameters looks like
robustness and is not. This is the single clearest argument for the Level 0 and Level 1
apparatus, and it is why nothing in findings 1–5 depends on the weighted model.

## 9. Partial moves from QWERTZ

Best layout differing from QWERTZ in at most *k* positions, optimised for simulated time
only.

| keys moved | train ms/char | test ms/char | vs QWERTZ | share of full gain | weak % |
|---|---|---|---|---|---|
| 2 | 34.515 | 34.595 | −4.2% | 38% | 40.5 |
| 4 | 33.638 | 33.711 | −6.7% | 59% | 42.0 |
| 6 | 32.629 | 32.767 | −9.3% | 83% | 45.5 |
| **8** | 32.203 | 32.249 | **−10.7%** | **95%** | 46.8 |
| 10 | 31.842 | 31.980 | −11.5% | 102% | 47.0 |
| 12 | 31.723 | 31.903 | −11.7% | 104% | 47.0 |
| 16 | 31.598 | 31.692 | −12.3% | 109% | 52.1 |
| 20 | 31.556 | 31.652 | −12.4% | 110% | 49.2 |
| 26 | 31.459 | 31.624 | −12.5% | 111% | 52.0 |
| 30 | 31.453 | 31.601 | −12.5% | 111% | 52.4 |

Shares above 100% occur because these are optimised for time alone while ZEHN is
constrained on four other measures — which is also the caveat: the weak-finger column
climbs to 47–52%, exactly the trade finding 3 objects to. A partial move worth making would
need the same constraint box applied.

## Files

| | |
|---|---|
| [`results/efficiency_log.txt`](results/efficiency_log.txt) | Levels 0 and 1, raw |
| [`results/final_log.txt`](results/final_log.txt) | the decisive constrained search |
| [`results/robustness_log.txt`](results/robustness_log.txt) | six workloads + parameter sweep |
| [`results/pareto_log.txt`](results/pareto_log.txt) | partial moves |
| [`results/sensitivity_log.txt`](results/sensitivity_log.txt) | weight perturbation |
| [`results/multiobj_log.txt`](results/multiobj_log.txt) | the nine-weighting search |
| [`results/optsim_log.txt`](results/optsim_log.txt) | pure-mechanics optimisation |
| [`results/frontier_log.txt`](results/frontier_log.txt) | unconstrained speed/load frontier |
| [`results/constrained_frontier_dev-at.tsv`](results/constrained_frontier_dev-at.tsv) | the frontier table, machine-readable |
