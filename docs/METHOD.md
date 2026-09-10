# Method

Everything in this study is reproducible from the code in `src/`. This file records what
was done and, more importantly, **why each check exists** — most of them exist because an
earlier version of the analysis was wrong in a way the check would have caught.

**Scope.** The subject is the *finger assignment* — which finger presses which key — on a
German/Austrian QWERTZ board. The letters never move. Sections 1, 3, 4, 5 and 6 below are
the shared measurement apparatus; section 10 is the assignment experiment itself. Sections
2 and 7 concern the layout question and are retained because the apparatus was built and
validated against it; see [APPENDIX-layout.md](APPENDIX-layout.md).

---

## 1. The physical keyboard

A German/Austrian **ISO 105-key (T1)** board, modelled in millimetres rather than as an
abstract grid, because row stagger is a real and asymmetric feature of the hardware.

Key pitch is 19.05 mm. Rows are offset by the width of the key that starts them:

| Row | Offset | Keys |
|---|---|---|
| number | 0.00u | `^ 1 2 3 4 5 6 7 8 9 0 ß ´` |
| top | 1.50u (Tab) | `q w e r t z u i o p ü +` |
| home | 1.75u (Caps) | `a s d f g h j k l ö ä #` |
| bottom | 1.25u (LShift) | `< y x c v b n m , . -` |

Finger assignment is the standard German ten-finger discipline. Home positions are
`a s d f` / `j k l ö`.

The consequences are not assumptions — they fall out of the geometry. Distance from the
home key, in millimetres:

```
top      q=19.6  w=19.6  e=19.6  r=19.6  t=23.8  z=30.5  u=19.6  i=19.6  o=19.6  p=19.6  ü=23.8
home     a= 0.0  s= 0.0  d= 0.0  f= 0.0  g=19.0  h=19.0  j= 0.0  k= 0.0  l= 0.0  ö= 0.0  ä=19.1
bottom   y=21.3  x=21.3  c=21.3  v=21.3  b=34.3  n=21.3  m=21.3  ,=21.3  .=21.3  -=21.3
```

`b` at 34.3 mm and `z` at 30.5 mm are the two worst keys on the board, and both are
reached by an index finger that has to travel diagonally inward. No opinion required.

**The optimisable set is 32 slots**: `q…ü` (11) + `a…ä` (11) + `y…-` (10). This is
exactly the slot set the Neo-family drivers use, which means every layout produced here
is a 32-character string that loads directly into an existing driver. It was chosen for
that reason and not for analytical convenience.

## 2. Reference layouts

QWERTZ plus the seven serious German-optimised layouts: **Neo2, Bone, AdNW, AdNWzjßf,
KOY, KOU, VOU**.

Their definitions were taken **verbatim from the neo2-llkh driver source** (`src/main.c`),
not from diagrams. An earlier attempt to read a layout off a rendered keyboard image
produced a bottom row with `w` and `l` duplicated from other rows — silently wrong, and
it would have contaminated every comparison. Machine-readable sources only.

Beating QWERTZ proves nothing. The bar throughout is **AdNW and KOY**.

## 3. Corpora and the train/test split

| | TRAIN (search sees this) | TEST (held out) |
|---|---|---|
| German | Buddenbrooks, Also sprach Zarathustra, Effi Briest, Werther — 2.26M chars | Faust, Die Verwandlung, Der Tod in Venedig, **+ 955 kB of modern German Wikipedia** — 1.11M total |
| English | Pride & Prejudice, Moby Dick, Sherlock Holmes, Frankenstein — 4.92M | A Tale of Two Cities, Alice, Great Expectations, **+ 514 kB of English Wikipedia** — 1.90M |
| Code | Python standard library, files 1–500 — 3.69M | Python standard library, files 501–900, disjoint — 3.42M |

A note on how those test figures came to be, because it is the kind of thing that is
usually quietly fixed: the Wikipedia download was still running when the corpus cache was
first built, so the initial run of the analysis used a German test set with only 432 kB of
Wikipedia and an English test set with **none at all**, while this document claimed
otherwise. The training corpora contain no Wikipedia and were unaffected, so no search was
re-run — but every held-out number was recomputed against the completed corpus. The
conclusions did not change; the figures moved by 0.1 to 0.8 points. The superseded numbers
are still in git history.

Default mix `dev-at` = **45% German / 30% English / 25% code**, for someone in Austria
writing prose in two languages and code in one. Other mixes are in `src/data.py` and the
conclusions were checked against them.

The German split is deliberately hostile to the optimiser: it trains on 19th-century
novels and is tested on contemporary encyclopaedic prose. The 1996 orthography reform
alone moves real probability mass off `ß`, so a layout that had merely memorised
Gutenberg's spelling would show it.

Text is folded to a 32-character alphabet (`a–z`, `ä ö ü ß`, comma, period) plus space.
Case is folded to lower — Shift is analysed separately in §8. Anything outside the
alphabet becomes a space, which models "some other key was pressed and the hands
returned", rather than pretending the surrounding characters were adjacent.

### What is deliberately excluded

`-` is not scored. QWERTZ has it in the main block; the Neo family has it on layer 3.
Charging one and not the other would be unfair, and modelling layer-3 holds inside the
letter analysis would muddle two separate questions. This mildly favours the Neo family,
and it is stated rather than hidden.

## 4. Three levels of assumption

The central methodological problem: **any optimiser will beat every existing layout on
its own scoring function.** That is a tautology. So results are reported at three
separate levels of assumption, and the reader can see which conclusions survive at which
level.

### Level 0 — no tunable parameters at all

Geometry and corpus counts only. Nothing here can be tuned to favour a layout.

- **Finger travel per character**, bracketed two ways because how far a hand drifts back
  toward home is genuinely unknown:
  - `HOVER` — a finger stays where it last pressed (skilled, minimal-motion typing)
  - `RETURN` — a finger returns home after every press (textbook technique)
  The truth is between. A layout that wins under both is genuinely moving fingers less.
- **Same-finger bigram rate** — how often one finger is asked to do two jobs in a row.
- **Forced serial travel** — millimetres a finger must cover between two keystrokes close
  enough in time that the movement cannot hide behind the other hand (lags 1–4).
- **Load distribution** — share of keystrokes per finger; weak-finger share (both pinkies
  and both ring fingers); hand imbalance.

### Level 1 — three physical constants, swept rather than chosen

A **parallel-finger simulator** (`src/simulate.py`). Ten fingers are independent
actuators. To press a key, the assigned finger travels from wherever it currently is,
then presses. Fingers move **concurrently** — while the right index types, the left
middle is already on its way. Keys are struck in text order and no faster than the motor
system can sequence them:

```
press[i] = max( press[i-1] + GAP,  free[finger] + travel_time(from, to) )
free[f]  = press[i] + DWELL
travel_time(d) = T_MOVE + SPEED * sqrt(d)        # ballistic: accelerate, then decelerate
```

Everything the hand-weighted models put in by hand falls out of this instead:

- a same-finger bigram is slow because one actuator must do two jobs in series
- alternating hands is fast because travel hides behind the other hand's work
- a long reach is free when the finger had idle time to prepare, and costly when it did not
- rolls are fast because adjacent fingers are already near their targets

Three parameters, all physical, all in units of time. Rather than pick values, the
analysis **sweeps 36 combinations** of `GAP × DWELL × (T_MOVE, SPEED)` and reports whether
the ranking ever changes.

### Level 2 — a hand-weighted effort model, reported but not relied upon

`src/metrics.py` contains a conventional weighted-sum effort model (pinky costs 1.75 of
an index, a same-finger bigram costs 4.0, a scissor 2.2). **These are my judgement, not
physics.** It is kept because it is what the layout literature uses and because the
comparison is instructive — but no conclusion in this paper rests on it. See §7 for what
happened when it *was* relied upon.

## 5. The closed form, and why it is trustworthy

Running the sequential simulator inside an annealer is far too slow. Its behaviour was
therefore derived in closed form. A keystroke is delayed only when the finger it needs is
still busy or still travelling; a finger that pressed L keystrokes ago has had L
sequencing intervals to arrive, so

```
stall(a, b, L) = max(0, DWELL + travel_time(distance(a,b)) - L*GAP)     # same finger only
ms_per_char    = GAP + Σ_L Σ_pairs  P(pair at lag L) · stall(pair, L)
```

This requires **lag-1 through lag-4 character-pair tables**, which the corpus module
builds over the keystroke sequence (so an intervening space still counts as a stroke).

**Validation** (`python src/simfast.py`), on 300k held-out German characters:

```
layout         simulator   closed form     diff
QWERTZ            48.513        49.025    0.512
Neo2              47.662        47.982    0.319
Bone              46.455        46.543    0.088
AdNW              46.241        46.287    0.046
AdNWzjßf          46.240        46.286    0.046
KOY               46.244        46.291    0.047
KOU               46.328        46.391    0.063
VOU               46.449        46.536    0.086

correlation 1.0000   ranking identical: True   MAE 0.151 ms/char
```

The closed form slightly overestimates because it ignores that a stall pushes later
keystrokes back, giving fingers extra time — a second-order effect that is largest for
the worst layout, so it is conservative in the direction that matters.

## 6. Sanity checks that had to pass before anything was designed

`python src/verify.py`:

1. **Fast scorer ≡ reference scorer.** Agreement to 1e-12 on the reference layouts and on
   40 random permutations. The first version disagreed by 3e-4; the cause was trigram
   pruning at 99.5% coverage, and the check is now run at full coverage with the pruning
   error reported separately (max 2.3e-4 relative, ranking preserved).
2. **Every layout is a valid permutation** covering `a–z ä ö ü ß , .` exactly once.
3. **Sign check.** The model must reproduce the known ordering of layouts people actually
   use, before it is allowed to design one:
   `AdNWzjßf < AdNW < KOY < KOU < VOU < Bone < Neo2 < QWERTZ < (deliberately awful)`.
   It does.

## 7. The negative result that reshaped the study

The first search optimised the Level-2 weighted model and produced a layout scoring
**4.7% better than the best published layout** on that model. It was wrong to report that
as an improvement, and the untuned measures showed why:

| | Level-2 effort | same-finger % | travel | Fitts-model WPM |
|---|---|---|---|---|
| the new layout | **−4.7%** | 1.61 (worse) | +1.2% (worse) | +0.1% (tie) |

It won on the objective it was optimised against and on nothing else. That is what
optimising your own scoring function looks like, and it is the reason the whole Level 0/1
apparatus exists. The result is kept in the repository rather than deleted.

## 8. Things a letter layout does not cover

Three effects were measured separately because they turn out to matter more than the
letter arrangement does for this user's actual workload:

- **The symbol layer** (`src/symbols.py`). On a German board `{ } [ ] \ @ ~ |` all require
  AltGr, a right-thumb key, and several land on the right hand as well. Measured on
  1.53M symbol keystrokes from the Python standard library.
  *An earlier version modelled AltGr as a right-pinky key and produced absurd costs
  (13.8 units for `\`). It is a thumb key; the corrected model is in the source.*
- **Shift discipline** (`src/shift_and_thumbs.py`). German capitalises every noun.
- **Backspace** (`src/shift_and_thumbs.py`). Cost of the corner reach versus a thumb key,
  with the break-even frequency computed rather than asserted.

## 9. The decisive experiment

Once Level 0 and Level 1 were in place, the question became precise and falsifiable:

> Is there a layout that matches AdNW on **every** awkwardness measure (home-row share,
> scissors, redirects) **and** on simulated time, while carrying substantially less load
> on the pinkies and ring fingers?

`src/final_search.py` answers it by hard constraint rather than by weighting. The
constraint box is set to **AdNW's own figures**; the weak-finger cap is tightened step by
step; the search either finds a layout inside the box or it does not. Nothing is traded
off against anything, so the answer cannot be manufactured by choosing a weight.

See [RESULTS.md](../RESULTS.md) for the answer.


---

## 10. The finger-assignment experiment

`src/fingersearch.py`.

**Parametrisation.** Fingers are ordered left to right and hands do not cross, so an
assignment is fully described by where the seven boundaries fall in each row:

```
LP | LR | LM | LI | RI | RM | RR | RP
```

Three letter rows, seven cuts each, 21 integers. The number row is not searched — it
follows the top row shifted one column, because it is staggered 1.5 u to the left, so
number key *i* sits above top-row key *i−1*. Almost no text drives it in any case, since
digits are stripped by the corpus normaliser.

**Resting positions follow the assignment.** A discipline that hands the left index three
home-row keys should not be scored as though the hand were still anchored at `F`. Each
finger rests on the home-row key it owns that is nearest its anatomical column (`A S D F` /
`J K L Ö`).

*An earlier version took the median owned key instead, which rested the left index on `G`
whenever it owned `F` and `G` — something no typist does, and it made the standard
discipline itself score as physically incredible. The anatomical-column rule replaced it.*

**Credibility filter.** An assignment is rejected if any finger owns no home-row key
(nowhere to rest) or if any key is more than 58 mm from its finger's resting key.

**Objective.** The parallel-finger simulator, unchanged, with no comfort weights. The
searches then run in three modes:

1. minimise time alone
2. minimise time subject to weak-finger load ≤ the standard discipline's
3. minimise time subject to weak-finger load **and** finger travel ≤ the standard's

Mode 3 is the decisive one. Travel is the parameter-free measure that catches the failure
mode of modes 1 and 2, which is that a search optimising simulated time will happily send
fingers on long journeys as long as those journeys hide behind the other hand's work. The
clock improves; the hand still moves.

**Single-key tests.** `src/keytweaks.py` moves exactly one key to an adjacent finger,
holding everything else fixed including the resting keys, and scores each on held-out text.
This asks the narrower question the whole-assignment search leaves open.

### What would falsify the conclusion

The claim is that the standard German assignment cannot be beaten on simulated time without
spending more finger travel or more weak-finger load. It is falsified by any assignment
that comes in strictly under all three of the standard's numbers. `fingersearch.py` prints
exactly that comparison and its verdict line.
