# Archive plan

Four copies, each pointing at the others. Nothing here has been created yet; the owner creates each one, in this order,
after approving the release candidate.

## 1. GitHub release tag

- Tag: **`perfect-lie-release-v1`** on the commit that adds `two_truths_lie_study/release/` and
  `two_truths_lie_study/writeup/`, on `RandallSPQR/edsl_wwil`. Create it after the release-candidate commit is merged
  and Tier 0 passes on that exact commit (`make reproduce`; `release/fresh_run/` holds the independent run).
- Release assets: the dataset archive (`perfect-lie-dataset-v1.tar.gz`, from `make dataset`), `TIER0_REPORT.md`, and
  `MANIFEST.sha256` of the dataset.
- Release notes: link to the three registration tags below, the Zenodo DOI, the Hugging Face dataset and the OSF
  project.
- Earlier tags (already on the remote; unchanged):

| tag | commit | what |
|---|---|---|
| `perfect-lie-prereg-v1` | `c2ca8b8` (annotated tag object `af64007`) | study 1 registration, revision 3 |
| `perfect-lie-reversed-prereg-v1` | `5261806` | reversed-note registration |
| `perfect-lie-phase2-prereg-v1` | `bc1c179` | Phase 2 registration, revision 4 |

## 2. Hugging Face dataset

- Repository (proposed): `RandallSPQR/perfect-lie` (dataset), private until the DOI exists, then public.
- Contents: the output of `make dataset` (`build/dataset/`; its `README.md` is the dataset card). Upload with
  `huggingface-cli upload RandallSPQR/perfect-lie build/dataset . --repo-type dataset`.
- Gating (recommended): "gated: auto" with the fabricated-content notice as the access prompt, so every download
  acknowledges it.
- Pin: record the dataset repository's commit hash in the GitHub release notes and on Zenodo.

## 3. Zenodo DOI

- Upload: the GitHub release's source archive (via the GitHub-Zenodo integration, or manually), plus the dataset
  archive. One DOI for the release version; Zenodo's concept DOI for all versions.
- Metadata: title, authors (owner), licence (owner's choice for the study materials; the dataset card's terms for the
  model outputs), related identifiers: the GitHub tag (isSupplementTo), the Hugging Face dataset (isIdenticalTo for
  the dataset part), each OSF registration (isDocumentedBy).
- After minting: put the DOI in `CITATION.cff`, the dataset card and the OSF project; that edit is a new commit and
  does not move the release tag.

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
