import asyncio
import hashlib
import os
from unittest.mock import MagicMock, patch

import pytest

from dictation_dad import tts


class TestTTS:
    def test_get_cache_path(self):
        path = tts._get_cache_path("hello")
        expected = os.path.join("./cache", hashlib.md5("hello".encode("utf-8")).hexdigest() + ".mp3")
        assert path == expected

    def test_get_voice_chinese(self):
        assert tts._get_voice("你好") == "zh-CN-XiaoxiaoNeural"

    def test_get_voice_english(self):
        assert tts._get_voice("hello") == "en-US-JennyNeural"

    def test_check_cache_exists(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts, "CACHE_DIR", str(tmp_path))
        text = "test"
        cache_path = tts._get_cache_path(text)
        os.makedirs(tmp_path, exist_ok=True)
        open(os.path.join(str(tmp_path), os.path.basename(cache_path)), "w").close()
        assert tts.check_cache(text) is True

    def test_check_cache_not_exists(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts, "CACHE_DIR", str(tmp_path))
        assert tts.check_cache("nonexistent") is False

    def test_get_missing_texts(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts, "CACHE_DIR", str(tmp_path))
        text1 = "existing"
        cache_path = tts._get_cache_path(text1)
        os.makedirs(tmp_path, exist_ok=True)
        open(os.path.join(str(tmp_path), os.path.basename(cache_path)), "w").close()
        missing = tts.get_missing_texts(["existing", "missing"])
        assert missing == ["missing"]

    @pytest.mark.asyncio
    async def test_generate_one_cache_exists(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts, "CACHE_DIR", str(tmp_path))
        text = "cached"
        cache_path = tts._get_cache_path(text)
        os.makedirs(tmp_path, exist_ok=True)
        open(os.path.join(str(tmp_path), os.path.basename(cache_path)), "w").close()
        with patch("dictation_dad.tts.edge_tts.Communicate") as mock:
            await tts._generate_one(text)
            mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_one_new(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts, "CACHE_DIR", str(tmp_path))
        text = "newtext"
        mock_comm = MagicMock()
        future = asyncio.Future()
        future.set_result(None)
        mock_comm.save = MagicMock(return_value=future)
        with patch("dictation_dad.tts.edge_tts.Communicate", return_value=mock_comm) as mock:
            await tts._generate_one(text)
            mock.assert_called_once()
            mock_comm.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_one_log_failure(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts, "CACHE_DIR", str(tmp_path))
        text = "logfail"
        mock_comm = MagicMock()
        future = asyncio.Future()
        future.set_result(None)
        mock_comm.save = MagicMock(return_value=future)
        with patch("dictation_dad.tts.edge_tts.Communicate", return_value=mock_comm):
            with patch("builtins.open", side_effect=OSError("disk full")):
                with pytest.raises(RuntimeError, match="写入生成日志失败"):
                    await tts._generate_one(text)

    @pytest.mark.asyncio
    async def test_generate_audios_empty(self):
        calls = []
        await tts.generate_audios([], lambda *args: calls.append(args))
        assert calls == [(0, 0, "")]

    @pytest.mark.asyncio
    async def test_generate_audios_with_callback(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts, "CACHE_DIR", str(tmp_path))
        mock_comm = MagicMock()
        future = asyncio.Future()
        future.set_result(None)
        mock_comm.save = MagicMock(return_value=future)
        with patch("dictation_dad.tts.edge_tts.Communicate", return_value=mock_comm):
            calls = []
            await tts.generate_audios(["a", "b"], lambda i, t, text: calls.append((i, t, text)))
            assert len(calls) == 3
            assert calls[0] == (0, 2, "a")
            assert calls[1] == (1, 2, "b")
            assert calls[2] == (2, 2, "")

    def test_get_audio_url(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tts, "CACHE_DIR", str(tmp_path))
        url = tts.get_audio_url("hello")
        assert url.startswith("file://")
        assert url.endswith(".mp3")
