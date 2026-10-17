"""Tests never spend money.

The study's tests run offline. This guard removes the OpenRouter key for every test, so any
code path that would reach a live model fails instead of billing. (Added after a test run sent
64 real elicitation calls, about $0.05, before the elicitation call was routed through the
adapter that tests replace with a fake.)
"""

import os
import tempfile

import pytest

# Second review, finding 6: EDSL writes to the user's config and cache directories (platformdirs) on
# import and when it sees an Expected Parrot key. Tests must not write credentials or depend on a
# writable home, so before any test module imports EDSL its directories point at a fresh temporary
# directory and the Expected Parrot key is removed from the test process.
_ISOLATED = tempfile.mkdtemp(prefix="perfect_lie_tests_")
for _v in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME"):
    os.environ[_v] = os.path.join(_ISOLATED, _v.lower())
os.environ.pop("EXPECTED_PARROT_API_KEY", None)


@pytest.fixture(autouse=True)
def _no_live_model_calls(monkeypatch):
    monkeypatch.delenv("OPEN_ROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("EXPECTED_PARROT_API_KEY", raising=False)
