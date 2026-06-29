from __future__ import annotations

from pathlib import Path

import pytest

from services.api.app import core


@pytest.fixture()
def isolated_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(core, "DB_PATH", tmp_path / "sqlite" / "app.db")
    monkeypatch.setattr(core, "RAW_DIR", tmp_path / "lesson_json" / "raw")
    monkeypatch.setattr(core, "NORMALIZED_DIR", tmp_path / "lesson_json" / "normalized")
    monkeypatch.setattr(core, "VALIDATED_DIR", tmp_path / "lesson_json" / "validated")
    monkeypatch.setattr(core, "EXPORT_DIR", tmp_path / "lesson_exports")
    monkeypatch.setattr(core, "WEB_PUBLIC_DIR", tmp_path / "web_public")
    monkeypatch.setattr(core, "WORD_IMAGE_DIR", tmp_path / "web_public" / "word_images")
    monkeypatch.setattr(core, "AUDIO_DIR", tmp_path / "web_public" / "audio")
    core.init_db(seed_test_data=True)
    return tmp_path
