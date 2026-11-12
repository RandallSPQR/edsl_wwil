# Independent Tier 0 runs

Each "attempt" is a fresh clone of the release candidate, reproduced by a separate agent session that was given only
`release/README.md` (no other context), on a 4-CPU Linux container. Attempts 2 and later used empty uv cache and Python
install directories, so `make env` downloaded Python 3.11 and every package itself.

| run | candidate commit | result | what it found |
|---|---|---|---|
| `attempt1/` | 2337e74 (local candidate) | **stopped at once** | the repository's root `.gitignore` excluded the release's own `*json`/`*csv`/`*txt`/`*png` files (EXPECTED.json, the claims manifest, the figures); fixed in `two_truths_lie_study/.gitignore` (REPRODUCTION_NOTES item 9) |
| `attempt2/` | 9dc154e (local candidate) | **PASS** in 1,589 s; 446 claims checked, every one matching; 37 files identical, 4 equal for documented reasons | README nits (disk estimate, claims count location, report rows without the model's directory), fixed |
| `docker_offline/` | the working tree after attempt 2 | numbers: every result and claim reproduced with `docker run --network none`; figures: 4 PNGs differed | the build machine's `/etc/matplotlib/matplotlibrc` had leaked into the figures; fixed (REPRODUCTION_NOTES item 10), then the write-up steps reproduced byte-identically in Docker (`docker_reproduce_writeup_after_fix.log`) |
| `final/` | cfcd870 (local candidate: the release's code and data) | **PASS** in 1,624 s (27 min 4 s wall clock); 446 claims checked, every one matching; 38 files identical, 4 equal for documented reasons; 22 GPU/API inputs sha256 ok | README: say how the uv route stays offline and which Python 3.11 patch releases work; added |

Candidate commits are local, unpushed commits of the release files on top of 66f6bf2. After cfcd870 only documentation
changed (this directory's logs, two README paragraphs, two `.gitignore` lines for the logs); Tier 0's code, data and
expected hashes are the same.
