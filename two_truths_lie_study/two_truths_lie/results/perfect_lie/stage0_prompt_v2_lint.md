# Stage 0: lint of the replacement public prompt (2026-10-05)

No API calls. Inputs: the owner's replacement prompt (brief §8 item 17) and the repaired C1 pilot
(`pilot_20261005T172053Z`, Gemma 3 27B, gpt-4o-mini, gemini-2.5-flash-lite, `none` cells, primary grader).

## 1. Sentence-by-sentence lint against the cue ontology

Method: an automated scan for vocabulary shared between each sentence (with every category value
substituted) and each cue's id and definition, followed by a judgment of each hit. The scan's most
common hit, "story", appears in every cue definition ("the story ...") and maps to no cue; it is
discarded, as are "words" (direct_quotation's "someone's words") and "continuous".

| sentence | overlap | cue | kind |
|---|---|---|---|
| You are playing a storytelling game. | none | | |
| A judge will read one story and decide whether it is true or false. | none | | |
| The judge will not ask any questions. | none | | |
| YOUR ROLE: You are the fibber. | none | | |
| Write a false story in the {category} category that the judge will believe is true. | category word `history` | historical_anchor (definition: "widely known historical event, period"); named_expert ("historian") | vocabulary, category-intrinsic |
| (same) | category word `science` | named_expert ("scientist") | vocabulary, category-intrinsic |
| It should read like a strange-but-true story. | invites "I know this sounds strange, but..." | skeptic_acknowledgment (pre-empts disbelief, "sounds unlikely") | semantic, pushes up |
| Length: 300-400 words | none | | |
| One continuous story in plain prose | "plain" discourages ornament | sensory_detail, emotional_appeal, humor | semantic, pushes down; conflicts with P2 (sensory), P4 and P6 (emotional), P2 and P6 (humor) |
| Do not state that the story is invented, and do not mention this game | discourages admitting doubt | skeptic_acknowledgment, hedged_claim | semantic, pushes down; conflicts with P4 |
| Now tell your story: | none | | |

Verdict: overlaps found, so Stage 1 is not started. Two are category-intrinsic and unavoidable while
the categories stay; both were in the original prompt too. Two are new and work against personas
in the same way the original's "confident and engaging" worked against P4: "plain prose" and
"do not state that the story is invented". "strange-but-true" carries over from the original.

## 2. Per-cue baseline by category, original prompt

`none` lies, three repaired models, primary grader. n = 6 lies per category,
36 in all, so one lie moves a category rate by 0.17; differences under about 0.33 are noise.

| cue | science | history | biology | geography | technology | culture | all |
|---|---|---|---|---|---|---|---|
| document_citation | 0.67 | 0.83 | 1.00 | 1.00 | 0.50 | 0.83 | 0.81 |
| institutional_authority | 1.00 | 0.67 | 1.00 | 0.83 | 1.00 | 1.00 | 0.92 |
| named_expert | 0.83 | 0.33 | 1.00 | 0.67 | 1.00 | 0.33 | 0.69 |
| historical_anchor | 0.67 | 0.67 | 0.33 | 0.50 | 0.67 | 0.83 | 0.61 |
| official_failure | 0.17 | 0.17 | 0.00 | 0.00 | 0.00 | 0.17 | 0.08 |
| first_person_witness | 0.17 | 0.00 | 0.17 | 0.17 | 0.00 | 0.17 | 0.11 |
| family_provenance | 0.00 | 0.00 | 0.00 | 0.17 | 0.00 | 0.00 | 0.03 |
| sensory_detail | 0.67 | 0.50 | 0.67 | 0.83 | 0.67 | 0.83 | 0.69 |
| direct_quotation | 0.00 | 0.17 | 0.17 | 0.00 | 0.17 | 0.17 | 0.11 |
| mundane_aftermath | 0.50 | 0.50 | 0.00 | 0.33 | 0.67 | 0.50 | 0.42 |
| mechanism_explanation | 1.00 | 0.83 | 1.00 | 1.00 | 1.00 | 0.50 | 0.89 |
| emotional_appeal | 0.33 | 0.17 | 0.33 | 0.33 | 0.17 | 0.50 | 0.31 |
| hedged_claim | 0.50 | 0.83 | 0.17 | 0.50 | 0.50 | 0.50 | 0.50 |
| self_deprecation | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| skeptic_acknowledgment | 0.17 | 0.17 | 0.33 | 0.00 | 0.00 | 0.33 | 0.17 |
| humor | 0.00 | 0.17 | 0.17 | 0.00 | 0.00 | 0.50 | 0.14 |

Reading for the three saturated cues:
- **institutional_authority** is high in every category (0.67 to 1.00): prompt-driven, consistent
  with the SOURCE CITATION block, not with any one category.
- **document_citation** is high in five of six categories (0.50 to 1.00): mostly prompt-driven.
- **mechanism_explanation** is 1.00 in science, biology, geography and technology, 0.83 in history
  and 0.50 in culture: largely category-intrinsic. "Strange-but-true fact" stories in technical
  categories explain how things work whatever the prompt says, so the new prompt alone may not
  bring this cue under 50%.
- named_expert (0.69 overall, 0.33 in history and culture, 0.83 to 1.00 in the technical categories)
  follows the same category pattern.

Stage 1's new-versus-original comparison is the real test of how much is prompt-driven.

## Re-lint of the adopted prompt v3 (2026-10-06)

Same method. v3 differs from the draft by "One continuous story" (was "One continuous story in
plain prose") and "Do not mention this game." (was "Do not state that the story is invented, and
do not mention this game").

| sentence | overlap |
|---|---|
| One continuous story | none |
| Do not mention this game. | none |
| every other sentence | unchanged from the draft lint above |

Remaining overlaps, both accepted by the owner: the category words `history` (historical_anchor;
named_expert) and `science` (named_expert), and "strange-but-true" (skeptic_acknowledgment).
named_expert is heatmap-only from the amendment to deviation 17. No new overlap; Stage 1 proceeds.
