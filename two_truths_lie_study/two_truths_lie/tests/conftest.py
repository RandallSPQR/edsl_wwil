"""Tests never spend money.

The study's tests run offline. This guard removes the OpenRouter key for every test, so any
code path that would reach a live model fails instead of billing. (Added after a test run sent
64 real elicitation calls, about $0.05, before the elicitation call was routed through the
adapter that tests replace with a fake.)
"""

import pytest


@pytest.fixture(autouse=True)
def _no_live_model_calls(monkeypatch):
    monkeypatch.delenv("OPEN_ROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
