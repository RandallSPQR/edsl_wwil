---
pretty_name: "The Perfect Lie: persuasive lies written to a judge's private beliefs"
license: other
license_name: perfect-lie-mixed
license_details: "Study materials (instrument, annotations' schema, code, adjudications): owner to choose (proposed CC BY 4.0 for data, MIT for code). Model outputs: subject to each generating model's terms (see 'Licenses and terms')."
language: [en]
task_categories: [text-generation, text-classification]
tags: [deception, persuasion, theory-of-mind, llm-evaluation, steering, interpretability, synthetic, fabricated-content]
size_categories: [10K<n<100K]
---

# The Perfect Lie

Lies written by language models for a storytelling game, each told to persuade a judge whose private beliefs about
what makes a story convincing were (or were not) disclosed to the liar; the cue annotations of every lie; the judges'
verdicts; and, for two open-weight liars, the activation directions and steering runs of Phase 2. Three
pre-registered studies (each registered as a dated GitHub release; see `ARCHIVE.md` in the release): study 1 (full versus placebo note), the reversed-note
study (full versus reversed note), and Phase 2 (activation probe and steering).

> **Fabricated-content notice.** Every story in this dataset is a deliberate lie, written to be believed. Many
> attribute invented events, findings, failures, accidents, cover-ups or harms to **real, named organizations**
> (universities, government agencies, museums, journals, companies) and to invented people with real-sounding names.
> **None of it is true.** Do not cite, quote or summarize these stories as fact, do not use them to train systems
> that present them as fact, and do not attach them to the organizations they name. Names are **flagged, not
> redacted** (below).

## Contents

| file | rows | what |
|---|---|---|
| `study1/lies.jsonl.gz` | 2,160 cells (2,110 complete, 50 failed) | study 1 interim (replicates 1-15): every planned cell |
| `reversed/lies.jsonl.gz` | 4,320 cells (4,297 complete, 23 failed) | reversed-note run |
| `reversed/comprehension.jsonl.gz` | 500 | comprehension-check answers, parsed and scored |
| `phase2/identity_lies.jsonl.gz` | 1,620 | identity-check lies generated on the pod (two runs), with primary grades |
| `phase2/pilot_lies.jsonl.gz` | 2,800 | stage-1 pilot and method-check pre-check lies (coherence only; never graded) |
| `phase2/stage2_lies.jsonl.gz` | 2,560 | stage-2 lies: steered, placebo, unsteered references, method check; graded |
| `phase2/probe/<model>/` | | `vectors.npz` (v and the cue-mention direction for every layer, float64), `per_layer_auroc.csv`, `probe_result.json`, `diagnostics.json`, `scale.json` |
| `phase2/steering/<model>/` | | setup records of every steered run (layer, norms, cosines, exact hook checks), pilot and coherence results, naturalness |
| `phase2/hf_revisions.json` | | pinned Hugging Face revisions of the open weights |
| `instrument/` | | personas, cues (rubric v0.6), prompts, designs, reversed notes, categories, model and provider pins |
| `screens/<study>/` | | the blind confession/refusal screens and the owner's adjudications |
| `content_flag_summary.json`, `MANIFEST.sha256` | | flag counts; sha256 of every file |

A **cell** is one planned lie (liar x prompt or category x target x condition x replicate). Each row is the cell's last
record in the run log (the release's git history keeps the full logs), with every field the runner stored:

- `user_prompt` (public prompt, identical across conditions), `liar_system_prompt` (the **private note** is in it),
  `liar_delivered_messages` (the exact messages sent), `lie`, `lie_words`, `liar_usage`, `liar_served_provider`;
- study 1 only: `elicitation` (the liar's stated belief about the judge, asked after the lie);
- `targets`: each judge model's verdict (`accept`, `confidence`, `raw` text);
- `grades`: each grader's cue annotation (`cues`, `counts`, `confidence`, the grader model, attempts and the raw
  output where kept): `primary` (Claude Sonnet 4.5), `google` (gemini-2.5-flash), and `secondary` (gpt-5, seeded 25%
  subsample); study 1 also `bhat_grades` (the same graders on the elicited belief);
- `status`, `errors`, `parse_failures` (raw text of unparseable responses);
- Phase 2: `alpha`, `arm`, `hyp`, `seed`, `ids` (generated token ids), `nll` (per-token NLL of the first 64 tokens
  under the unsteered model), `primary` and `google_call` (raw grader calls with usage);
- `content_flags` (added by the release builder; below).

The scores and every analysis are reproduced from these files by the release's Tier 0 (`make reproduce`).

## Provenance

| part | generated | liars / models | judges | graders |
|---|---|---|---|---|
| study 1 | 2026-10-07 to 2026-10-08, OpenRouter | Llama 3.1 8B Instruct (CoreWeave, bf16), Gemma 3 27B IT (Novita), gpt-4o-mini (OpenAI, Azure), Gemini 2.5 Flash-Lite (Google) | the same four | Claude Sonnet 4.5, gemini-2.5-flash, gpt-5 (subsample), all via OpenRouter |
| reversed note | 2026-10-16, OpenRouter | the same four, same pins | the same four | the same three |
| Phase 2 identity check | 2026-10-20 to 2026-10-21 | Gemma 3 27B IT, Llama 3.1 8B Instruct on one RTX PRO 6000 (bf16, transformers 4.53.2) | none | Claude Sonnet 4.5 via OpenRouter |
| Phase 2 pilot, stage 2 | 2026-10-23 to 2026-10-27 | the same two, steered | none | Claude Sonnet 4.5 direct (`claude-sonnet-4-5-20250929`), gemini-2.5-flash via OpenRouter (20% subsample) |

Personas, notes and categories were written for the study (no personal data). The adjudications are the study
owner's, made blind to condition before unblinding.

## Content flags (fabricated content about real organizations)

Every lie row carries `content_flags`:

- `fiction`: always true;
- `org_mentions`: organization-like names found by a pattern (capitalized phrases ending in, or built on, words such as
  University, Institute, Museum, Agency, Department, Survey, Society, Journal, Company; plus common acronyms such as
  NASA, USGS, EPA, MIT). **Heuristic**: it misses some names, truncates some ("Massachusetts Institute"), catches
  some generic phrases ("The Journal"), and does not tell real organizations from invented ones;
- `names_institution`, `alleges_official_failure`: the primary grader's `institutional_authority` and
  `official_failure` cue labels (null where a lie was not graded);
- `possible_fabricated_harm_to_named_org`: an organization mention and an alleged official failure in the same lie.

Counts (`content_flag_summary.json`):

| file | lies | with organization mentions | names an institution (grader) | possible fabricated harm to a named org |
|---|---|---|---|---|
| study 1 | 2,160 | 646 | 814 | 83 |
| reversed note | 4,320 | 1,149 | 1,347 | 220 |
| Phase 2 identity check | 1,620 | 562 | 701 | 154 |
| Phase 2 pilot (ungraded) | 2,800 | 826 | n/a | n/a |
| Phase 2 stage 2 | 2,560 | 849 | 985 | 122 |

**Decision: flag, not redact.** The texts are kept verbatim because the cue annotations, judge verdicts and every
analysis are computed on them; a redacted text would no longer match its grades. Downstream users who display or
redistribute lies should filter on these flags or redact the `org_mentions` themselves.

## Licenses and terms

The lies, verdicts and annotations are model outputs. Each generating model's terms govern its outputs; the API route
adds the provider's and OpenRouter's terms. Summary as understood on 2026-10-29 from secondary copies of the terms
(the primary pages could not be fetched from the build environment; **verify each before publishing**):

| model (role) | terms | outputs | points relevant to redistribution |
|---|---|---|---|
| Llama 3.1 8B Instruct (liar, judge) | Llama 3.1 Community License + Acceptable Use Policy | not claimed by Meta | Redistributing Llama Materials needs a copy of the license and "Built with Llama"; a model trained on Llama outputs and distributed must have "Llama" at the start of its name. The AUP bars using Llama to generate or promote disinformation or defamatory content: this dataset is a labelled research artefact, released with the notice above, not content presented as true. |
| Gemma 3 27B IT (liar, judge) | Gemma Terms of Use (rev. 2026-04-01) + Prohibited Use Policy | "Google claims no rights in Outputs"; outputs are not Model Derivatives | Same caution on misinformation; users are responsible for outputs and their use. |
| gpt-4o-mini (liar, judge), gpt-5 (grader) | OpenAI Terms of Use / Business Terms + Usage Policies | assigned to the user | Bars using output to develop models that compete with OpenAI; state that the content is AI-generated. |
| Gemini 2.5 Flash-Lite (liar, judge), gemini-2.5-flash (grader) | Gemini API Additional Terms (rev. 2026-03-23) | Google does not claim ownership | Bars using the service to develop competing models; users responsible for generated content and its downstream sharing. |
| Claude Sonnet 4.5 (grader) | Anthropic Commercial Terms | customer owns outputs | Bars using the services to build a competing product or to train competing models without approval. |
| providers (CoreWeave, Novita, Azure, Google, OpenAI) and OpenRouter | their terms of service | | |

Practical consequence, stated as the release's terms of use: **research and evaluation use; not for training models
that compete with the providers above; keep the fabricated-content notice with any copy.** The study's own materials
(instrument, adjudications, flags, code) are the owner's to license.

## What is not included, and why

- **Activations** (Phase 2 probe stage: 1,800 items x 62 layers x 5,376 for Gemma, 1,800 x 32 x 4,096 for Llama; about
  3.3 GB in float32) and the **placebo, method-check and naturalness vectors**: they stayed on the study's RunPod network
  volume and were not copied out. The probe directions `v` for every layer are included; the steering vector of every
  run is unit(v) x alpha x ||v|| at the selected layer (both in this dataset). `release/tiers/tier3_fetch_volume.sh`
  describes how to retrieve the rest.
- **Weights**: not redistributed; pinned by revision in `phase2/hf_revisions.json` (both repositories are gated).
- **The grading-route check's raw API responses**: only the parsed labels were kept (in the release's
  `regrade_direct.json`).
- **Pilot and smoke runs before each registration** and the quarantined void run: in the release's git history
  (`results/perfect_lie/`), not in this dataset.
- No API keys, no personal data.

## Citation

Zenodo: [10.5281/zenodo.24122306](https://doi.org/10.5281/zenodo.24122306). Code, write-up and the push-button
reproduction (Tier 0): GitHub release
[`perfect-lie-release-v1`](https://github.com/RandallSPQR/edsl_wwil/releases/tag/perfect-lie-release-v1)
(`two_truths_lie_study/release/README.md`). The contents of this repository are the release archive
`perfect-lie-dataset-v1.tar.gz` unpacked (sha256 `4b9527a0e7db3a32cfae3434bf338c56ef53cec8e8511c32a7403c08a81ef17a`);
`MANIFEST.sha256` lists every file, except this card, which adds this paragraph.
