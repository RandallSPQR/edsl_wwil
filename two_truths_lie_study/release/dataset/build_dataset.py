"""Build the release dataset of The Perfect Lie from the released files (no model calls, no network).

  python release/dataset/build_dataset.py [--out DIR]      (default: two_truths_lie_study/build/dataset)

Layout (each table is gzipped JSON Lines; one row per planned cell, the last record of each cell in the run log):
  instrument/                 personas, cues (rubric v0.6), prompts, design, reversed notes, categories, model pins
  study1/lies.jsonl.gz        every lie of the interim (replicates 1-15): prompts, private note, delivered messages,
                              lie, elicitation, raw judge verdicts (4 judges), raw grader output (primary, gpt-5,
                              Google), failures and parse failures
  reversed/lies.jsonl.gz      every lie of the reversed-note run, same fields
  reversed/comprehension.jsonl.gz  every comprehension-check answer, parsed and scored
  phase2/identity_lies.jsonl.gz    identity-check pod lies (both runs) with their primary grades
  phase2/pilot_lies.jsonl.gz       stage-1 pilot lies (retired and Addendum 5 placebo) and method-check pre-check lies,
                                   with per-token NLL; never graded
  phase2/stage2_lies.jsonl.gz      every stage-2 cell: lie, NLL, raw primary and Google grader output
  phase2/probe/<model>/            v and the cue-mention direction per layer (vectors.npz), per-layer AUROC table
                                   (per_layer_auroc.csv), probe_result.json, diagnostics.json, scale.json
  phase2/steering/<model>/         the setup records of every steered run (layer, norms, cosines, hook checks)
  phase2/hf_revisions.json         pinned Hugging Face revisions of the open weights
  screens/                    the blind confession/refusal screens and the owner's adjudications, per study
Every lie row carries `content_flags` (see the dataset card): the lies are fiction written to deceive a judge, and many
attribute invented events, failures or harms to real, named organizations. Names are flagged, not redacted.
Writes MANIFEST.sha256 last.
"""
import argparse, csv, gzip, hashlib, json, re, shutil
from pathlib import Path

REL = Path(__file__).resolve().parents[1]
STUDY = REL.parent
R = STUDY / "two_truths_lie" / "results"
D = STUDY / "two_truths_lie" / "data"
SLUGS = ["gemma-3-27b-it", "llama-3.1-8b-instruct"]

# Organization-like names: a run of capitalized words ending in (or starting with) an organizational head noun.
ORG_HEAD = (r"University|Institute|Institution|Museum|Agency|Department|Ministry|Bureau|Office|Service|Survey|"
            r"Society|Association|Council|Commission|Committee|Authority|Board|Foundation|Trust|College|Academy|"
            r"Hospital|Clinic|Laboratory|Laboratories|Library|Archive|Archives|Observatory|Company|Corporation|Inc|"
            r"Ltd|Co|Group|Center|Centre|Administration|Organization|Organisation|Federation|Union|Church|Navy|Army|"
            r"Police|Court|Parliament|Congress|Senate|Times|Post|Journal|Gazette|Press|Network|Bank|Railway|Railroad|"
            r"Airlines|Records")
CAP = r"(?:[A-Z][\w'&.-]+|of|the|for|and|de|du|des|la|le)"
ORG_RE = re.compile(rf"\b(?:(?:[A-Z][\w'&.-]+\s)(?:{CAP}\s)*(?:{ORG_HEAD})\b|(?:{ORG_HEAD})\s(?:of|for)\s(?:the\s)?(?:[A-Z][\w'&.-]+\s?)+)")
ACRONYM_RE = re.compile(r"\b(?:NASA|FBI|CIA|NSA|FDA|EPA|CDC|NIH|NOAA|USGS|USDA|UNESCO|WHO|UN|NATO|BBC|NHS|MIT|"
                        r"IBM|FAA|NTSB|OSHA|IRS|DOE|DOD|MI5|MI6|KGB|Interpol|Smithsonian)\b")


def org_mentions(text):
    if not text:
        return []
    found = {m.group(0).strip() for m in ORG_RE.finditer(text)} | {m.group(0) for m in ACRONYM_RE.finditer(text)}
    return sorted(found)


def content_flags(text, cues):
    """cues: the primary grader's cue labels for this lie (or None)."""
    orgs = org_mentions(text)
    cues = cues or {}
    return {
        "fiction": True,
        "org_mentions": orgs,
        "names_institution": bool(cues.get("institutional_authority")) if cues else None,
        "alleges_official_failure": bool(cues.get("official_failure")) if cues else None,
        "possible_fabricated_harm_to_named_org": bool(orgs) and bool(cues.get("official_failure")) if cues else None,
    }


def read_jsonl(p):
    op = gzip.open if p.suffix == ".gz" else open
    with op(p, "rt") as f:
        return [json.loads(l) for l in f if l.strip()]


def last_per_cell(rows, key="cell_id"):
    last = {}
    for r in rows:
        last[r[key]] = r
    return list(last.values())


def write_jsonl(p, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(p, "wb", mtime=0) as g:
        for r in rows:
            g.write((json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n").encode())
    return len(rows)


def primary_cues(r):
    g = (r.get("grades") or {}).get("primary") or {}
    return g.get("cues")


def build(out):
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    counts = {}

    # instrument
    for d, files in ((D / "perfect_lie", ["personas.json", "cues.json", "prompts.json", "design.json", "models.json",
                                          "run_locks.json"]),
                     (D / "perfect_lie_reversed", ["reversed_notes.json", "categories.json", "category_draw.json",
                                                   "design.json", "run_config.json"])):
        for f in files:
            dst = out / "instrument" / d.name / f
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(d / f, dst)

    # study 1 and the reversed note: the last record per cell, every field, plus content flags
    for name, src in (("study1/lies.jsonl.gz", R / "perfect_lie/full_interim_r01-15/records.jsonl.gz"),
                      ("reversed/lies.jsonl.gz", R / "perfect_lie_reversed/full_run/main/records.jsonl.gz")):
        rows = last_per_cell(read_jsonl(src))
        for r in rows:
            r["content_flags"] = content_flags(r.get("lie"), primary_cues(r))
        counts[name] = write_jsonl(out / name, rows)
    rows = last_per_cell(read_jsonl(R / "perfect_lie_reversed/full_run/comprehension/records.jsonl.gz"))
    counts["reversed/comprehension.jsonl.gz"] = write_jsonl(out / "reversed/comprehension.jsonl.gz", rows)

    # phase 2
    ident = []
    for run in ("pod_run", "pod_run_novita"):
        for r in last_per_cell(read_jsonl(R / f"phase2/identity_check/{run}/records.jsonl")):
            r["identity_run"] = run
            r["content_flags"] = content_flags(r.get("lie"), primary_cues(r))
            ident.append(r)
    counts["phase2/identity_lies.jsonl.gz"] = write_jsonl(out / "phase2/identity_lies.jsonl.gz", ident)
    pil = []
    for s in SLUGS:
        for f, phase in (("records.jsonl.gz", "pilot (Addendum 4)"), ("records_placebo2.jsonl.gz", "pilot placebo rerun (Addendum 5)"),
                         ("mc_precheck_records.jsonl.gz", "method-check coherence pre-check (Addendum 7)")):
            for r in read_jsonl(R / f"phase2/pilot/{s}/{f}"):
                r["phase"] = phase
                r["content_flags"] = content_flags(r.get("text"), None)
                pil.append(r)
    counts["phase2/pilot_lies.jsonl.gz"] = write_jsonl(out / "phase2/pilot_lies.jsonl.gz", pil)
    st = []
    for s in SLUGS:
        for r in read_jsonl(R / f"phase2/stage2/{s}/graded.jsonl.gz"):
            r["content_flags"] = content_flags(r.get("text"), (r.get("grade") or {}).get("cues"))
            st.append(r)
    counts["phase2/stage2_lies.jsonl.gz"] = write_jsonl(out / "phase2/stage2_lies.jsonl.gz", st)

    for s in SLUGS:
        p = out / "phase2/probe" / s
        p.mkdir(parents=True)
        for f in ("vectors.npz", "probe_result.json", "diagnostics.json", "scale.json", "PROBE.md", "DIAGNOSTICS.md"):
            shutil.copy2(R / f"phase2/probe/{s}/{f}", p / f)
        pr = json.loads((R / f"phase2/probe/{s}/probe_result.json").read_text())
        with open(p / "per_layer_auroc.csv", "w", newline="") as f:
            w = csv.writer(f)
            # one row per candidate layer x test; the gate's tests (held-out personas, wordings A-C) and the cue-mention
            # control (recorded as uninformative by design, Addendum 3; ci is its 90% interval)
            w.writerow(["layer", "selected", "layer_passes_gate", "v_norm", "test", "auroc", "ci_low", "ci_high",
                        "ci_level", "test_verdict"])
            for L, d in sorted(pr["per_layer"].items(), key=lambda x: int(x[0])):
                tests = {"held_out_personas": d.get("held_out_personas"),
                         **{f"held_out_wordings_{k}": v for k, v in (d.get("held_out_wordings") or {}).items()},
                         "cue_mention_control": d.get("control")}
                for t, v in tests.items():
                    if not isinstance(v, dict):
                        continue
                    ci, lvl = (v["ci90"], 90) if "ci90" in v else (v.get("ci95") or [None, None], 95)
                    verdict = v.get("verdict", v.get("passes", ("inside band" if v.get("inside_band") else "outside band")
                                                         if "inside_band" in v else None))
                    w.writerow([L, int(L) == pr["selected_layer"], d.get("passes"), d.get("v_norm"), t, v.get("auroc"),
                                ci[0], ci[1], lvl, verdict])
        q = out / "phase2/steering" / s
        q.mkdir(parents=True)
        for f in ("setup.json", "setup_placebo2.json", "mc_precheck_setup.json", "pilot_result.json", "pilot2_result.json",
                  "mc_precheck.json"):
            shutil.copy2(R / f"phase2/pilot/{s}/{f}", q / f"pilot_{f}" if not f.startswith(("pilot", "mc_")) else q / f)
        for f in ("setup.json", "coherence.json", "natural.json", "grading_summary.json"):
            shutil.copy2(R / f"phase2/stage2/{s}/{f}", q / f"stage2_{f}")
    for f in ("category_split.json",):
        shutil.copy2(R / f"phase2/probe/{f}", out / "phase2" / f)
    shutil.copy2(R / "phase2/pilot/confirmatory_alphas.json", out / "phase2/confirmatory_alphas.json")
    shutil.copy2(R / "phase2/grader_robustness/subsample.json", out / "phase2/google_subsample_cells.json")
    shutil.copy2(REL / "dataset/hf_revisions.json", out / "phase2/hf_revisions.json")

    # screens and adjudications
    for study, files in (("study1", [R / "perfect_lie/interim_look/blind_text_screens.json",
                                     R / "perfect_lie/interim_look/blind_text_screens.md",
                                     R / "perfect_lie/interim_look/screen_adjudication.json"]),
                         ("reversed", [R / "perfect_lie_reversed/final_analysis/blind_text_screens.md",
                                       R / "perfect_lie_reversed/final_analysis/screen_matches_key.json",
                                       R / "perfect_lie_reversed/final_analysis/screen_adjudication.json"]),
                         ("phase2", [R / "phase2/stage2/screen_matches.json", R / "phase2/stage2/screen_matches_key.json",
                                     R / "phase2/stage2/screen_adjudication.json"])):
        for f in files:
            dst = out / "screens" / study / f.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst)

    # card and flag summary
    shutil.copy2(REL / "dataset/DATASET_CARD.md", out / "README.md")
    flags = {}
    for name in ("study1/lies.jsonl.gz", "reversed/lies.jsonl.gz", "phase2/identity_lies.jsonl.gz",
                 "phase2/pilot_lies.jsonl.gz", "phase2/stage2_lies.jsonl.gz"):
        rows = read_jsonl(out / name)
        f = [r["content_flags"] for r in rows]
        flags[name] = {"rows": len(rows), "with_org_mentions": sum(bool(x["org_mentions"]) for x in f),
                       "names_institution": sum(bool(x["names_institution"]) for x in f),
                       "possible_fabricated_harm_to_named_org": sum(bool(x["possible_fabricated_harm_to_named_org"]) for x in f)}
    (out / "content_flag_summary.json").write_text(json.dumps(flags, indent=1) + "\n")
    lines = []
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.sha256":
            lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out)}")
    (out / "MANIFEST.sha256").write_text("\n".join(lines) + "\n")
    return counts, flags


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=STUDY / "build" / "dataset")
    a = ap.parse_args()
    counts, flags = build(a.out.resolve())
    print(json.dumps({"rows": counts, "content_flags": flags}, indent=1))
    print(f"dataset written to {a.out}")
