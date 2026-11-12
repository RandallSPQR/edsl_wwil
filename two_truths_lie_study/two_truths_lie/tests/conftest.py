"""Tests never spend money.

The study's tests run offline. This guard removes the OpenRouter key for every test, so any
code path that would reach a live model fails instead of billing. (Added after a test run sent
64 real elicitation calls, about $0.05, before the elicitation call was routed through the
adapter that tests replace with a fake.)
"""

import os
import tempfile

import pytest

# Reviews 2 and 3, finding 6: EDSL writes to per-user directories on import and when it sees an
# Expected Parrot key (credential file, cache databases, logs). Tests must not write credentials or
# depend on a writable home on ANY platform, so before any test module imports EDSL:
#   * HOME points at a fresh temporary directory: EDSL's Path.home()/expanduser paths, and
#     platformdirs on macOS (~/Library/...), resolve under it;
#   * the XDG variables point there too (Linux platformdirs);
#   * platformdirs' user_*_dir/_path functions are replaced, so no platform-specific rule can escape;
#   * EDSL's own path settings (cache and SQLList databases, log directory) are set explicitly;
#   * the Expected Parrot key is removed.
# test_perfect_lie_test_isolation.py asserts that every resolved path is under ISOLATED_ROOT.
import pathlib

import platformdirs

ISOLATED_ROOT = pathlib.Path(tempfile.mkdtemp(prefix="perfect_lie_tests_")).resolve()
os.environ["PERFECT_LIE_TEST_ROOT"] = str(ISOLATED_ROOT)
os.environ["HOME"] = str(ISOLATED_ROOT / "home")
os.makedirs(os.environ["HOME"], exist_ok=True)
for _v in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME"):
    os.environ[_v] = str(ISOLATED_ROOT / _v.lower())


def _isolated_dir(kind):
    def f(appname=None, *args, **kwargs):
        d = ISOLATED_ROOT / "platformdirs" / kind / (appname or "")
        if kwargs.get("ensure_exists"):
            d.mkdir(parents=True, exist_ok=True)
        return str(d)
    return f


for _kind in ("data", "config", "cache", "state", "log", "runtime"):
    _f = _isolated_dir(_kind)
    setattr(platformdirs, f"user_{_kind}_dir", _f)
    setattr(platformdirs, f"user_{_kind}_path", (lambda f: lambda *a, **k: pathlib.Path(f(*a, **k)))(_f))

os.environ["EDSL_DATABASE_PATH"] = f"sqlite:///{ISOLATED_ROOT / 'edsl' / 'lm_model_calls.db'}"
os.environ["EDSL_SQLLIST_DB_PATH"] = f"sqlite:///{ISOLATED_ROOT / 'edsl' / 'sql_list_data.db'}"
os.environ["EDSL_LOG_DIR"] = str(ISOLATED_ROOT / "edsl" / "logs")
os.makedirs(ISOLATED_ROOT / "edsl" / "logs", exist_ok=True)
os.environ.pop("EXPECTED_PARROT_API_KEY", None)


@pytest.fixture(autouse=True)
def _no_live_model_calls(monkeypatch):
    monkeypatch.delenv("OPEN_ROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("EXPECTED_PARROT_API_KEY", raising=False)
