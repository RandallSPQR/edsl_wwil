# Archive

Four copies, each pointing at the others. GitHub, Hugging Face and Zenodo are done; the OSF links remain for the
owner (section 4).

## 1. GitHub release (done)

- Tag **`perfect-lie-release-v1`** on `4e6069a` (`RandallSPQR/edsl_wwil`, branch `claude/confident-babbage-fljgmx`),
  the commit that adds `two_truths_lie_study/release/` and `two_truths_lie_study/writeup/`. Tier 0 passed on that
  commit's code and data (`release/fresh_run/final/`). Release page: https://github.com/RandallSPQR/edsl_wwil/releases/tag/perfect-lie-release-v1
- Assets: `perfect-lie-dataset-v1.tar.gz` (sha256 `4b9527a0e7db3a32cfae3434bf338c56ef53cec8e8511c32a7403c08a81ef17a`)
  and its `.sha256`.
- Later commits on the branch (such as the one adding the DOI to these files) do not move the tag.
- Earlier tags (unchanged):

| tag | commit | what |
|---|---|---|
| `perfect-lie-prereg-v1` | `c2ca8b8` (annotated tag object `af64007`) | study 1 registration, revision 3 |
| `perfect-lie-reversed-prereg-v1` | `5261806` | reversed-note registration |
| `perfect-lie-phase2-prereg-v1` | `bc1c179` | Phase 2 registration, revision 4 |

## 2. Hugging Face dataset (done)

- https://huggingface.co/datasets/RandallSPQR/perfect-lie (public; gated access with automatic approval). Contents: `perfect-lie-dataset-v1.tar.gz` unpacked; its
  `README.md` is the dataset card with the DOI added to its citation section. Upload commit `902feac`, every file
  verified byte-identical after upload.

## 3. Zenodo (done)

- DOI: [10.5281/zenodo.24122306](https://doi.org/10.5281/zenodo.24122306).
- Cite the DOI for the release; `CITATION.cff` carries it.

## 4. OSF links

OSF URLs are not stored in the repository; the owner fills the column below from the OSF project, and the table goes
into the GitHub release notes and the Zenodo record.

| item | registration text in the repository | commit or record | OSF URL |
|---|---|---|---|
| Study 1 registration (rev. 3) | `PREREG_DRAFT.md` | tag `perfect-lie-prereg-v1` (`c2ca8b8`) | _owner_ |
| Study 1 Addendum 1 (conditions fix, sequential code, non-viable rule) | `PERFECT_LIE.md` item 29 | recorded 2026-10-06 | _owner_ |
| Study 1 Addendum 2 (transport retry) | `PERFECT_LIE.md` item 30 | recorded 2026-10-08 | _owner (confirm the number)_ |
| Study 1 Addendum 3 (estimates, tipping point, empty-cue breakdown, confession rule) | `PERFECT_LIE.md` items 32-34 | before unblinding, 2026-10-08 | _owner_ |
| Study 1 results | `two_truths_lie/results/perfect_lie/final_analysis/final_report.md` | 2026-10-09 | _owner_ |
| Reversed-note registration | `PREREG_REVERSED.md` | tag `perfect-lie-reversed-prereg-v1` (`5261806`) | _owner_ |
| Reversed-note Addendum 1 (review fixes, screen adjudication) | `PERFECT_LIE.md` item 37 | cites `465ae50` | _owner_ |
| Reversed-note results post | `two_truths_lie/results/perfect_lie_reversed/final_analysis/final_report.md` | posted 2026-10-20 | _owner_ |
| Phase 2 registration (rev. 4) | `PREREG_PHASE2.md` | tag `perfect-lie-phase2-prereg-v1` (`bc1c179`) | _owner_ |
| Phase 2 Addendum 1 (probe-stage code) | `PREREG_PHASE2_ADDENDA.md` | `630fb00` | _owner_ |
| Phase 2 Addendum 2 (Google subsample) | same | `22427c7` | _owner_ |
| Phase 2 Addendum 3 (diagnostics, OpenRouter exception) | same | `2b47b53` | _owner_ |
| Phase 2 Addendum 4 (pilot code; two hook-check revisions) | same | `2e99e06`, `b372c2b`, `21a1c1f` | _owner_ |
| Phase 2 Addendum 5 (new placebo) | same | `ccd787c` | _owner_ |
| Phase 2 Addendum 6 (stage-2 analysis and grading code) | same | `b389b68` | _owner_ |
| Phase 2 Addendum 7 (stage-2 generation; method check per target) | same | `6133228` | _owner_ |
| Phase 2 Addendum 8 (generation failures as cells) | same | `f4a70a7`, text fix `482fce9` | _owner_ |
| Phase 2 results | `two_truths_lie/results/phase2/stage2/STAGE2_RESULTS.md` | `66f6bf2` | _owner_ |
| Write-up (Methods, Findings, figures) | `writeup/` | release commit | _owner_ |
