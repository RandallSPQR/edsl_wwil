"""Reviews 2 and 3, finding 6: tests must write no credentials and nothing outside a temporary
directory, on any platform. Asserts that every per-user path EDSL resolves is under the conftest's
isolated root."""

import os
from pathlib import Path

import platformdirs

ISOLATED_ROOT = Path(os.environ["PERFECT_LIE_TEST_ROOT"])   # set by tests/conftest.py


def _inside(p) -> bool:
    p = str(p)
    if p.startswith("sqlite:///"):
        p = p[len("sqlite:///"):]
    return Path(p).resolve().is_relative_to(ISOLATED_ROOT)


def test_home_and_platformdirs_resolve_inside_the_test_directory():
    assert _inside(Path.home()) and _inside(os.path.expanduser("~"))
    for kind in ("data", "config", "cache", "state", "log"):
        assert _inside(getattr(platformdirs, f"user_{kind}_dir")("edsl")), kind


def test_edsl_credential_cache_and_log_paths_resolve_inside_the_test_directory():
    from edsl.config import CONFIG, cache_dir
    from edsl.coop.ep_key_handling import ExpectedParrotKeyHandler
    assert _inside(cache_dir)
    assert _inside(ExpectedParrotKeyHandler().config_dir)
    for k in ("EDSL_DATABASE_PATH", "EDSL_SQLLIST_DB_PATH", "EDSL_LOG_DIR"):
        assert _inside(CONFIG.get(k)), k
    assert "EXPECTED_PARROT_API_KEY" not in os.environ


def test_storing_a_key_writes_only_inside_the_test_directory():
    from edsl.coop.ep_key_handling import ExpectedParrotKeyHandler
    h = ExpectedParrotKeyHandler()
    h.store_ep_api_key("test-key-not-real")
    assert _inside(h.config_dir) and (Path(h.config_dir) / h.ep_key_file_name).exists()
