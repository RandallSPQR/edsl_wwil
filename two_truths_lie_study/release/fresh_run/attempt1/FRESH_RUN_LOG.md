# Fresh-clone Tier 0 run: log

- Date/time (UTC): 2026-10-29, started 18:17:57Z, finished 18:18:54Z
- Reproducer: an independent agent that had not seen the project before. Its only documentation was `two_truths_lie_study/release/README.md`.
- Clone: `/tmp/claude-0/-home-user-edsl-wwil/4699dee8-10e0-5f40-a807-efe82da6461d/scratchpad/fresh_run/edsl_wwil`
  (this clone replaces the README's `git clone` and `git checkout perfect-lie-release-v1` steps, because that tag does not exist yet)
- Clone commit (`git rev-parse HEAD`): `2337e740d2d40c0cc5e53f2e25be5cc55c63f0bf` ("release candidate (local, not pushed)"),
  branch `claude/confident-babbage-fljgmx`, origin `.../scratchpad/candidate_repo`

## Machine

```
$ nproc
4
$ uname -a
Linux vm 6.18.44-fc-v185 #1 SMP PREEMPT_DYNAMIC @0 x86_64 x86_64 x86_64 GNU/Linux
$ uv --version
uv 0.11.32 (x86_64-unknown-linux-gnu)
```

## Commands

The working directory for both commands was `<clone>/two_truths_lie_study`.

### 1. `make env`

- Start: 2026-10-29T18:18:02Z, end: 2026-10-29T18:18:02Z (real 0.098 s), exit code **0**
- Note: it took 0.1 s because the packages were already in uv's local cache on this machine. The README says this step uses the network once, but this run did not download anything, so it does not test a cold network install.

```
cd release && UV_PROJECT_ENVIRONMENT=.venv uv sync --frozen --python 3.11
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
Using CPython 3.11.15
Creating virtual environment at: .venv
Installed 22 packages in 54ms
 + contourpy==1.3.3
 + cycler==0.12.1
 + fonttools==4.68.0
 + formulaic==1.2.2
 + interface-meta==2.0.1
 + kiwisolver==1.5.1
 + matplotlib==3.11.2
 + narwhals==2.28.0
 + numpy==2.4.6
 + packaging==26.3
 + pandas==2.3.3
 + patsy==1.0.3
 + pillow==13.0.0
 + pyparsing==3.3.3
 + python-dateutil==3.0.0
 + pytz==2026.6
 + scipy==1.17.1
 + six==1.17.0
 + statsmodels==0.15.0
 + typing-extensions==4.16.0
 + tzdata==2026.6
 + wrapt==2.5.1

real	0m0.098s
user	0m0.037s
sys	0m0.165s
EXIT=0
```

(The `UV_NATIVE_TLS` warning comes from this machine's environment, not from the repository.)

### 2. `make reproduce`

- Command: `(time make reproduce) > fresh_run/make_reproduce.out 2>&1; echo EXIT=$?`, run in the background
- Start: 2026-10-29T18:18:07Z, end: 2026-10-29T18:18:07Z, exit code **2** (make), measured wall clock **0.051 s**
- Full output (it is short):

```
release/.venv/bin/python release/tier0/reproduce.py --work build/tier0 --perm-chunks 1
Traceback (most recent call last):
  File ".../edsl_wwil/two_truths_lie_study/release/tier0/reproduce.py", line 308, in <module>
    main()
  File ".../edsl_wwil/two_truths_lie_study/release/tier0/reproduce.py", line 209, in main
    pins = json.loads((REL / "tier0" / "EXPECTED.json").read_text())["environment"]
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/.local/share/uv/python/cpython-3.11.15-linux-x86_64-gnu/lib/python3.11/pathlib.py", line 1058, in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
  File "/root/.local/share/uv/python/cpython-3.11.15-linux-x86_64-gnu/lib/python3.11/pathlib.py", line 1044, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
FileNotFoundError: [Errno 2] No such file or directory: '.../edsl_wwil/two_truths_lie_study/release/tier0/EXPECTED.json'
make: *** [Makefile:18: reproduce] Error 1

real	0m0.051s
user	0m0.038s
sys	0m0.011s
EXIT=2
```

The run did not create `build/`, so it wrote no `TIER0_REPORT.md` or `tier0_report.json`. I ran `make reproduce` once and did not retry it, because the only fix (adding the missing file) is forbidden by the rules of this run.

### 3. Diagnosis (read-only; no files edited)

I looked beyond the README only to find out why the file was missing:

- `ls release/tier0`: it holds `make_expected.py`, `netguard/`, `perm_chunk.py`, `rebuild_*.py` and `reproduce.py`. There is **no `EXPECTED.json`**.
- `git check-ignore -v two_truths_lie_study/release/tier0/EXPECTED.json` gives `.gitignore:13:*json`. The repository's root `.gitignore`
  (inherited from the parent edsl repo) ignores `*json`, `*csv`, `*txt`, `*png`, `*gz`, `*jsonl`, `*svg`, `*html` and more, so these files were
  never committed. (The raw records `*.jsonl.gz` are tracked: there are 15 of them, so they must have been force-added. The other files were not.)
- I compared this with the author's working tree (`/home/user/edsl_wwil`) by running `git ls-files --others --ignored --exclude-standard two_truths_lie_study`,
  leaving out `.venv`, `build/` and `__pycache__`. I listed only file names and did not read any contents. 24 files exist there that are ignored and untracked.
  The full list is in `fresh_run/ignored_in_original.txt`. These release and write-up files are among them and are missing from a clone:
  - `release/tier0/EXPECTED.json`: the immediate cause of the failure
  - `release/tier0/inputs/regrade_direct_rows.json`
  - `release/dataset/hf_revisions.json` (the README's Layout section lists it)
  - `release/requirements.lock.txt` (the README's Layout section lists it for the pip route)
  - `release/environment_evidence/probe_output.txt`
  - `writeup/CLAIMS_MANIFEST.csv` (the README calls it the claims manifest)
  - `writeup/check_output.txt`, `writeup/derived/levels.json`
  - `writeup/figures/fig1..fig4_*.png` (the README's four figures)
  - The other 12 are uncompressed `*.jsonl` copies of raw records whose `.jsonl.gz` versions are tracked, so a clone probably does not need them.
- `release/fresh_run/`, which the README's Layout section lists, is not in the clone either. That may be expected, since this run is what produces it.
- `git status --short` in the clone after the run shows nothing apart from the ignored `release/.venv/`. The clone was not modified.

## TIER0_REPORT.md

None was written. `make reproduce` aborted before it created `build/tier0/`.

## Measured wall-clock runtime of `make reproduce`

0.051 s. It aborted at once. The README's figure of about 27 minutes (1,596 s) could not be tested.

## Verdict

- **(a) PASS or FAIL:** Tier 0 printed neither `PASS` nor `FAIL`. It **failed** before doing any work. `reproduce.py` crashed with
  `FileNotFoundError` on `release/tier0/EXPECTED.json`, and make exited with code 2.
- **(b) Claims manifest:** the claims check never ran, so no claims were checked. There is no claims-checker output to quote. Also, `writeup/CLAIMS_MANIFEST.csv`
  is not in the clone.
- **(c) Rebuilt files not "identical":** none were rebuilt, so there is nothing to compare.
- **(d) README problems for a newcomer:**
  1. **Blocking: the clone lacks files the README and Tier 0 need.** `release/tier0/EXPECTED.json` (which the README describes as holding "pins and sha256 of every
     released file"), `release/requirements.lock.txt`, `release/dataset/hf_revisions.json`, `writeup/CLAIMS_MANIFEST.csv` and the four figures are
     all ignored by the root `.gitignore` (`*json`, `*txt`, `*csv`, `*png`) and were never committed. Following the README on a clean clone fails at
     `make reproduce`. This is a packaging error in the commit rather than a mistake in the README text, but the README promises these files.
  2. `release/fresh_run/` is listed in the Layout section but is not in the clone.
  3. The README says `make env` needs the network once. On this machine uv's cache was already warm, so this run did not exercise a cold download.
     That is a limitation of this test, not a README error.
  4. The README is otherwise clear and short. Its three commands map directly onto `make env` and `make reproduce`, and it says where the report is written.
     This run could not assess the claims about runtime, PASS criteria or "equal; ..." vintages.
