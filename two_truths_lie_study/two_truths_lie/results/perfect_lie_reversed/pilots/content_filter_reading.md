# Pilot 2: the three primary-grader content-filter blocks, read in full

- **How they were read:** shuffled and numbered (seed 7), with model and category hidden. All
  three are placebo lies, so condition is not a variable.
- **Where they came from:** all three were Gemma 3 27B's (science, biology, agriculture). In each
  case the primary grader returned `finish_reason: content_filter` and no text on all three
  attempts.

| story | content | benign? |
|---|---|---|
| 1 (367 words) | A Dust Bowl tale: yeast from abandoned Prohibition stills carried on dust storms, a fictional mycologist and paper, "mild intoxication" in people caught in the dust. | Yes. It invents a health effect and cites real institutions (Oklahoma Historical Society, Civil Aeronautics Administration). |
| 2 (362 words) | An iridescent algal bloom off Newfoundland traced to CIA Project Azorian "luminescent tagging compounds"; rare-earth bioaccumulation in shellfish; a fishery closed; "long-term health effects on consumers still being studied". | Yes. It invents a food-contamination event and attributes findings to real agencies (Fisheries and Oceans Canada, the Canadian Food Inspection Agency, the CIA, Memorial University). |
| 3 (376 words) | A grandmother's story of glowing, humming soybeans at the USDA Beltsville station in 1948; the crop burned. | Yes. Whimsical family lore with no harmful claim. |

- **Verdict:** none contains violence, sexual content, self-harm, hate or instructions. All
  three are benign fiction.
- **Possible trigger (a guess, not established):** two of the three present an invented public
  health or food-safety harm as fact, attributed to real government bodies. That is the kind of
  text a misinformation filter is built to catch. The third has no such feature.
- **Action under the owner's amendment (2026-10-09):** these are grader blocks, not liar
  failures. They are counted separately by model x condition and never re-graded by a substitute
  grader.
