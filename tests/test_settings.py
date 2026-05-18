import os

import pytest
import yaml

from dictation_dad.settings import DEFAULT_SETTINGS, Settings


class TestSettings:
    def test_init_file_not_exists(self, tmp_path):
        filepath = tmp_path / "nonexistent.yaml"
        s = Settings(str(filepath))
        assert s.to_dict() == DEFAULT_SETTINGS

    def test_init_file_exists_valid(self, tmp_path):
        filepath = tmp_path / "settings.yaml"
        data = {"audio_duration_factor": 2.0, "extra_wait_time": 5.0}
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f)
        s = Settings(str(filepath))
        assert s.get("audio_duration_factor") == 2.0
        assert s.get("extra_wait_time") == 5.0
        assert s.get("min_wait_time") == DEFAULT_SETTINGS["min_wait_time"]

    def test_init_file_exists_none_content(self, tmp_path):
        filepath = tmp_path / "settings.yaml"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("")
        s = Settings(str(filepath))
        assert s.to_dict() == DEFAULT_SETTINGS

    def test_init_file_exists_invalid_yaml(self, tmp_path):
        filepath = tmp_path / "settings.yaml"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("{invalid")
        s = Settings(str(filepath))
        assert s.to_dict() == DEFAULT_SETTINGS

    def test_save_creates_file(self, tmp_path):
        filepath = tmp_path / "settings.yaml"
        s = Settings(str(filepath))
        s.set("audio_duration_factor", 2.5)
        s.save()
        assert os.path.exists(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
        assert loaded["audio_duration_factor"] == 2.5

    def test_save_creates_directory(self, tmp_path):
        filepath = tmp_path / "sub" / "settings.yaml"
        s = Settings(str(filepath))
        s.save()
        assert os.path.exists(filepath)

    def test_get_existing_key(self, tmp_path):
        filepath = tmp_path / "settings.yaml"
        s = Settings(str(filepath))
        assert s.get("audio_duration_factor") == DEFAULT_SETTINGS["audio_duration_factor"]

    def test_get_nonexistent_key(self, tmp_path):
        filepath = tmp_path / "settings.yaml"
        s = Settings(str(filepath))
        assert s.get("nonexistent") is None

    def test_set_valid_key(self, tmp_path):
        filepath = tmp_path / "settings.yaml"
        s = Settings(str(filepath))
        s.set("audio_duration_factor", 3.0)
        assert s.get("audio_duration_factor") == 3.0

    def test_set_invalid_key(self, tmp_path):
        filepath = tmp_path / "settings.yaml"
        s = Settings(str(filepath))
        s.set("invalid_key", 123)
        assert s.get("invalid_key") is None

    def test_to_dict_returns_copy(self, tmp_path):
        filepath = tmp_path / "settings.yaml"
        s = Settings(str(filepath))
        d = s.to_dict()
        d["audio_duration_factor"] = 999
        assert s.get("audio_duration_factor") == DEFAULT_SETTINGS["audio_duration_factor"]
