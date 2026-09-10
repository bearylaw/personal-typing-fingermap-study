# Reproducing this study

Python 3.12, `numpy`, `matplotlib`. Nothing else. No GPU, no network beyond the corpus
download. The whole study runs in about 45 minutes on one core.

```bash
git clone https://github.com/<you>/public-keyboard-paper
cd public-keyboard-paper/src
pip install numpy matplotlib
```

## Step 0 — fetch the corpora

The texts are not committed (≈14 MB, and the Wikipedia portion is CC BY-SA, which is
easier to respect by pointing at the source than by vendoring it).

```bash
python fetch_corpus.py      # Project Gutenberg, by ID — deterministic
python fetch_wiki.py        # Wikipedia random sample — NOT deterministic, see below
```

`fetch_corpus.py` pulls exact Project Gutenberg IDs, so it reproduces byte-for-byte:

| Split | ID | Work |
|---|---|---|
| de_train | 34811 | Buddenbrooks |
| de_train | 7205 | Also sprach Zarathustra |
| de_train | 5323 | Effi Briest |
| de_train | 2407 | Die Leiden des jungen Werther |
| de_test | 2229 | Faust I |
| de_test | 22367 | Die Verwandlung |
| de_test | 12108 | Der Tod in Venedig |
| en_train | 1342, 2701, 1661, 84 | Pride & Prejudice, Moby Dick, Sherlock Holmes, Frankenstein |
| en_test | 98, 11, 1400 | A Tale of Two Cities, Alice, Great Expectations |

The code corpus is the Python standard library on the machine running the study — files
1–500 for training, 501–900 for test, sorted by path, `__pycache__` and `test` directories
excluded. It therefore varies slightly with the Python version; 3.12.10 was used here.

**The Wikipedia portion is a random sample and will differ on every run.** The run
reported here used 432,494 characters of German and 500k of English. If you want to check
that this does not matter, run the study with `--profile german` against the Gutenberg-only
German test set; the ranking is unchanged.

## Step 1 — verify before believing anything

```bash
python verify.py
```

Must print `ALL CHECKS PASSED`. This confirms:

- the vectorised scorer agrees with the readable one to 1e-12, on the reference layouts
  and on 40 random permutations
- every layout is a valid permutation of the 32-character alphabet
- the model reproduces the published ordering of existing layouts
  (`AdNW < KOY < Bone < Neo2 < QWERTZ < deliberately-awful`)

If the sign check fails, nothing downstream is meaningful.

```bash
python simfast.py
```

Must print `correlation 1.0000  ranking identical: True`. This confirms the closed-form
stall model matches the sequential simulator on held-out text.

## Step 2 — measure the existing layouts

```bash
python efficiency.py dev-at
```

Produces the Level-0 table (no tunable parameters) and the Level-1 sweep over 36
parameter combinations. This is the evidence for findings 1–3 in [RESULTS.md](../RESULTS.md).

## Step 3 — the searches, in the order they were actually run

```bash
python optimize.py    dev-at 10 300000   # Level-2 weighted model — the negative result
python multiobj.py    dev-at 3  220000   # 9 weightings, judged on untuned criteria
python optimize_sim.py dev-at 6 300000   # pure mechanics, no comfort terms
python frontier.py    dev-at 3  220000   # speed vs weak-finger load frontier
python final_search.py dev-at 5 260000   # the decisive constrained search
```

Each writes a `result_*.txt` / `frontier_*.txt` holding 32-character layout strings.

Annealing is seeded, so runs reproduce. Convergence is reported as the spread across
restarts — for the main search, sd 4.8 effort units on a ~1640 total, i.e. the search
finds the same basin every time.

## Step 4 — the separate effects

```bash
python symbols.py            # AltGr vs layer 3, on 1.53M symbol keystrokes
python shift_and_thumbs.py   # German capitalisation; backspace break-even
python anglemod.py dev-at    # ISO angle mod
```

## Step 5 — figures

```bash
python plots.py dev-at
```

Writes `figures/fig1..fig6`. The categorical palette is validated CVD-safe on all pairs;
every meaningful point is directly labelled so identity never depends on colour alone.

## Step 6 — robustness

```bash
python sensitivity.py dev-at 400 0.40
```

Perturbs every weight in the Level-2 model by ±40%, 400 times, and recomputes the ranking
on held-out text. Reported as win rate and mean rank. This exists to show which
conclusions depend on the weighted model — the Level-0 and Level-1 conclusions do not
depend on it at all, which is the point.

## What would falsify the main finding

The claim is that a layout exists which matches AdNW on home-row share, scissors,
redirects and simulated time while carrying materially less weak-finger load.

It is falsified if `final_search.py` reports `no` in the feasibility column at every cap
below AdNW's own 41.7% — that is, if tightening the weak-finger constraint always forces
one of the other measures out of the box. The run reported here does not, but the check is
one command and the constraint box is set from AdNW's numbers, not chosen by hand.
