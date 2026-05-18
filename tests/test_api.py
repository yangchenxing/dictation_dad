import asyncio
from unittest.mock import patch

import pytest

from dictation_dad.api import API, TTSProgressTracker
from dictation_dad.file_manager import FileManager


class TestTTSProgressTracker:
    def test_callback_and_get(self):
        tracker = TTSProgressTracker()
        tracker.callback(1, 3, "hello")
        p = tracker.get()
        assert p["current"] == 1
        assert p["total"] == 3
        assert p["text"] == "hello"
        assert p["done"] is False
        assert p["error"] is None

    def test_finish(self):
        tracker = TTSProgressTracker()
        tracker.finish()
        assert tracker.get()["done"] is True

    def test_fail(self):
        tracker = TTSProgressTracker()
        tracker.fail("error")
        p = tracker.get()
        assert p["done"] is True
        assert p["error"] == "error"


class TestAPI:
    def test_list_directory_success(self, tmp_path, monkeypatch):
        api = API()
        monkeypatch.setattr(api, "file_manager", FileManager(str(tmp_path)))
        (tmp_path / "dir1").mkdir()
        res = api.list_directory("")
        assert res["success"] is True
        assert len(res["data"]["directories"]) == 1

    def test_list_directory_failure(self):
        api = API()
        res = api.list_directory("..")
        assert res["success"] is False
        assert "非法路径" in res["error"]

    def test_create_directory_success(self, tmp_path, monkeypatch):
        api = API()
        monkeypatch.setattr(api, "file_manager", FileManager(str(tmp_path)))
        res = api.create_directory("", "newdir")
        assert res["success"] is True
        assert (tmp_path / "newdir").exists()

    def test_create_directory_failure(self):
        api = API()
        res = api.create_directory("", "bad name")
        assert res["success"] is False
        assert "非法字符" in res["error"]

    def test_delete_file_success(self, tmp_path, monkeypatch):
        api = API()
        monkeypatch.setattr(api, "file_manager", FileManager(str(tmp_path)))
        (tmp_path / "test.ch_word.csv").write_text("speech\n苹果\n")
        res = api.delete_file("test.ch_word.csv")
        assert res["success"] is True

    def test_delete_file_failure(self):
        api = API()
        res = api.delete_file("nonexistent.ch_word.csv")
        assert res["success"] is False

    def test_preview_csv_success(self, tmp_path, monkeypatch):
        api = API()
        monkeypatch.setattr(api, "file_manager", FileManager(str(tmp_path)))
        (tmp_path / "test.ch_word.csv").write_text("speech\n苹果\n")
        res = api.preview_csv("test.ch_word.csv")
        assert res["success"] is True
        assert len(res["data"]) == 1

    def test_preview_csv_failure(self):
        api = API()
        res = api.preview_csv("nonexistent.csv")
        assert res["success"] is False

    def test_upload_csv_success(self, tmp_path, monkeypatch):
        api = API()
        monkeypatch.setattr(api, "file_manager", FileManager(str(tmp_path)))
        content = "speech\n苹果\n"
        res = api.upload_csv("", "test.ch_word.csv", content)
        assert res["success"] is True

    def test_upload_csv_invalid_extension(self):
        api = API()
        res = api.upload_csv("", "test.txt", "hello")
        assert res["success"] is False
        assert "扩展名" in res["error"]

    def test_upload_csv_invalid_content(self):
        api = API()
        content = "answer\napple\n"
        res = api.upload_csv("", "test.ch_word.csv", content)
        assert res["success"] is False
        assert "内容不合规" in res["error"]

    def test_upload_csv_exists(self, tmp_path, monkeypatch):
        api = API()
        monkeypatch.setattr(api, "file_manager", FileManager(str(tmp_path)))
        (tmp_path / "test.ch_word.csv").write_text("speech\n苹果\n")
        content = "speech\n香蕉\n"
        res = api.upload_csv("", "test.ch_word.csv", content, overwrite=False)
        assert res["success"] is False
        assert res.get("exists") is True

    def test_upload_csv_overwrite(self, tmp_path, monkeypatch):
        api = API()
        monkeypatch.setattr(api, "file_manager", FileManager(str(tmp_path)))
        (tmp_path / "test.ch_word.csv").write_text("speech\n苹果\n")
        content = "speech\n香蕉\n"
        res = api.upload_csv("", "test.ch_word.csv", content, overwrite=True)
        assert res["success"] is True

    def test_upload_csv_unexpected_error(self, tmp_path, monkeypatch):
        api = API()
        monkeypatch.setattr(api, "file_manager", FileManager(str(tmp_path)))
        from unittest.mock import patch
        with patch.object(api.file_manager, "save_file", side_effect=RuntimeError("disk error")):
            res = api.upload_csv("", "test.ch_word.csv", "speech\n苹果\n")
            assert res["success"] is False
            assert "disk error" in res["error"]

    def test_get_dictation_info_success(self, tmp_path, monkeypatch):
        api = API()
        monkeypatch.setattr(api, "file_manager", FileManager(str(tmp_path)))
        (tmp_path / "test.ch_word.csv").write_text("speech\n苹果\n")
        res = api.get_dictation_info("test.ch_word.csv")
        assert res["success"] is True
        assert res["data"]["missing_count"] == 1
        assert "entries" in res["data"]
        assert "play_params" in res["data"]

    def test_get_dictation_info_failure(self):
        api = API()
        res = api.get_dictation_info("invalid.txt")
        assert res["success"] is False

    def test_start_pre_generate_no_missing(self, tmp_path, monkeypatch):
        api = API()
        monkeypatch.setattr(api, "file_manager", FileManager(str(tmp_path)))
        (tmp_path / "test.ch_word.csv").write_text("speech\n苹果\n")
        with patch("dictation_dad.api.get_missing_texts", return_value=[]):
            res = api.start_pre_generate("test.ch_word.csv")
            assert res["success"] is True
            assert res["data"]["started"] is False

    def test_start_pre_generate_with_missing(self, tmp_path, monkeypatch):
        api = API()
        monkeypatch.setattr(api, "file_manager", FileManager(str(tmp_path)))
        (tmp_path / "test.ch_word.csv").write_text("speech\n苹果\n")
        async def mock_generate(*a, **k):
            return None
        with patch.object(api.executor, "submit", lambda f: f()):
            with patch("dictation_dad.api.generate_audios", mock_generate):
                res = api.start_pre_generate("test.ch_word.csv")
                assert res["success"] is True
                assert res["data"]["started"] is True
                assert res["data"]["total"] == 1

    def test_start_pre_generate_task_failure(self, tmp_path, monkeypatch):
        api = API()
        monkeypatch.setattr(api, "file_manager", FileManager(str(tmp_path)))
        (tmp_path / "test.ch_word.csv").write_text("speech\n苹果\n")
        async def mock_generate(*a, **k):
            raise RuntimeError("tts failed")
        with patch.object(api.executor, "submit", lambda f: f()):
            with patch("dictation_dad.api.generate_audios", mock_generate):
                res = api.start_pre_generate("test.ch_word.csv")
                assert res["success"] is True
                assert res["data"]["started"] is True
                # 此时 tts_tracker 应该记录了错误
                progress = api.get_pre_generate_progress()
                assert progress["data"]["error"] == "tts failed"
                assert progress["data"]["done"] is True

    def test_start_pre_generate_failure(self):
        api = API()
        res = api.start_pre_generate("invalid.txt")
        assert res["success"] is False

    def test_get_pre_generate_progress_none(self):
        api = API()
        res = api.get_pre_generate_progress()
        assert res["success"] is True
        assert res["data"]["done"] is True

    def test_get_pre_generate_progress_running(self, tmp_path, monkeypatch):
        api = API()
        monkeypatch.setattr(api, "file_manager", FileManager(str(tmp_path)))
        (tmp_path / "test.ch_word.csv").write_text("speech\n苹果\n")
        async def mock_generate(*a, **k):
            return None
        with patch.object(api.executor, "submit", lambda f: f()):
            with patch("dictation_dad.api.generate_audios", mock_generate):
                api.start_pre_generate("test.ch_word.csv")
                res = api.get_pre_generate_progress()
                assert res["success"] is True

    def test_get_settings(self):
        api = API()
        res = api.get_settings()
        assert res["success"] is True
        assert "audio_duration_factor" in res["data"]

    def test_save_settings(self, tmp_path, monkeypatch):
        api = API()
        monkeypatch.setattr(api.settings, "filepath", str(tmp_path / "settings.yaml"))
        res = api.save_settings({"audio_duration_factor": 2.0})
        assert res["success"] is True
        assert api.settings.get("audio_duration_factor") == 2.0
