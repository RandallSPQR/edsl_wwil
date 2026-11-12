# Write-up package: Why Would I Lie (WWIL), Phases 1-3

The paper draft, the Methods and Findings sections and the figures. The phases are registered as study 1 (Phase 1),
the reversed-note study (Phase 2) and "Phase 2" (Phase 3, the probe and steering); each phase's section names its
registration. The author writes the motivation, introduction and discussion in `sections/`.

| file | what |
|---|---|
| `PAPER.md` | the paper in reading order: `sections/00-02`, the phase table, then per phase its Methods, Findings and figures (verbatim from the files below), then `sections/03_discussion.md` |
| `sections/*.md` | the author's sections (title, motivation: The Perfect Lie, WWIL introduction, discussion), each starting as notes with sources; not checked |
| `METHODS.md`, `FINDINGS.md` | the two generated sections |
| `FIGURES.md` | captions: n, test, source file and full sha256 |
| `figures/fig1-4*.png` | the four figures |
| `CLAIMS_MANIFEST.csv` | one row per number (and per verified fact) in the three texts |
| `check_output.txt` | the checker's output for this version |

## Rebuild and check

```
python derive_levels.py     # descriptive s levels for figures 2 and 3 -> derived/levels.json
python build.py             # texts, figures, manifest, PAPER.md (rerun after editing sections/)
python check_claims.py      # must print PASS
```

Run from this directory. The two-truths-lie package must be importable (`derive_levels.py` uses the registered scoring
code), along with numpy, scipy and matplotlib.

## Conventions

- **No hand-typed numbers.** `build.py` writes every number through `claims.py`. A claim is one of:
  - a value at a JSON Pointer in a committed results file (`json_path` column; ` x100` marks a percentage);
  - a formula over such values (`expr: ...`, for example a one-sided lower bound or a count of true flags);
  - a design constant quoted verbatim from a registration text (`text: "..."`).
- **Facts are claims too.** Statements such as "converged", "rejections preserved" or "flagged" are rendered from the
  results files, as yes/no or as counts like "2 of 4". They are never written as prose.
- **Labels** (`label` column):
  - registered primary;
  - registered secondary (including registered robustness, sensitivity and descriptive analyses, and those added by
    a dated addendum before unblinding);
  - post hoc (descriptive): after unblinding, or added before unblinding but labelled not pre-registered;
  - exploratory;
  - design constant (registration).
- **The manifest.** `sentence` is the full rendered line holding the claim (one sentence, bullet or table row per
  line). `offset_in_sentence` gives the value's position in that line.
- **Not checked as claims:**
  - identifiers: model names, section, addendum and log-item numbers, H1/H2, P1-P6, rubric v0.6, revision numbers;
  - the 95% and 90% CI descriptors and `K − 1`;
  - anything in backticks (paths, hashes, formulas).
- **Spelled-out numbers** are structural counts (four liars, five targets, three conditions, one-sided). The checker
  lists them for review.
- **Figures** are drawn by `build.py` from the same files. The few registration constants in figure text (alpha 1,
  0.05) go through the same quote check.
  - Model order and colours are fixed in every figure: Llama 3.1 8B `#4e79a7`, Gemma 3 27B `#f28e2b`, gpt-4o-mini
    `#e15759`, Gemini 2.5 Flash-Lite `#76b7b2`.
  - Figures 2 and 3 share one s axis.
- **Levels in figures 2 and 3 are post hoc and descriptive.** The registrations report contrasts, not levels. Each
  level is the mean over categories of the per-category mean over personas or targets, with a 95% t interval
  (K − 1 df). `derive_levels.py` computes them from the committed lie-level records with each study's registered
  scoring code. The checker re-derives them and compares.

## What the checker does

`check_claims.py` re-reads every source from disk. It re-implements the value lookup rather than importing
`claims.py`. It checks:

1. each source's sha256 against the manifest;
2. each value against its pointer, formula or quote, within display rounding;
3. that each sentence is a line of its file, with the value at its recorded offset;
4. that every number in the three texts is a claim value or a whitelisted identifier;
5. that the texts are byte-identical to a fresh render;
6. that `levels.json` matches a fresh derivation from the records;
7. that every figure exists.

It exits non-zero on any failure. Tamper tests (a hand-typed number, an altered manifest value, an edited sentence)
each fail it.

## Study 1 addendum numbering

The study 1 addenda are not stored as separate files. The texts cite them with their entries in `PERFECT_LIE.md`:

- Addendum 1: log item 29;
- Addendum 2: log item 30 (transport retry);
- Addendum 3: log items 32-34.

`final_report.md` names Addenda 1 and 3 explicitly. The mapping of Addendum 2 to item 30 follows the
log's order and dates (`release/ARCHIVE.md`, section 4).
