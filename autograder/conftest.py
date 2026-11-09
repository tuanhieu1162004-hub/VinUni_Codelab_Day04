"""Keep test-created tickets in a fresh temporary data directory per test."""

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "starter-code"))
import tools


@pytest.fixture(autouse=True)
def isolated_data(tmp_path, monkeypatch):
    for source in (ROOT / "raw-data").glob("*.json"):
        shutil.copy2(source, tmp_path / source.name)
    monkeypatch.setattr(tools, "RAW_DATA_DIR", str(tmp_path))
    return tmp_path
